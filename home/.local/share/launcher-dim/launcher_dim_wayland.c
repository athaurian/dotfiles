/* Full-screen dim layer behind a launcher command.
 *
 * Connects to Wayland directly instead of using a toolkit. GTK startup alone
 * costs about 60 ms.
 *
 * The sheet waits for the launcher to map. sway's IPC tree gives a layer
 * surface a non-zero extent only once it is mapped, so the helper polls
 * GET_TREE while the launcher starts and commits the sheet when a layer
 * surface that was not mapped before appears. That lands the sheet a few
 * milliseconds after the launcher's own buffer commit, instead of a whole
 * launcher startup ahead of it. Without sway IPC, or when the launcher never
 * maps, the sheet is committed at once instead.
 */

#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include <wayland-client.h>

#include "wlr-layer-shell-unstable-v1-client-protocol.h"

/* How long the launcher may take to map before the sheet is shown anyway. */
#define LAUNCHER_MAP_TIMEOUT_MS 300
#define LAUNCHER_POLL_NS 2000000

static struct wl_compositor *compositor;
static struct wl_shm *shm;
static struct zwlr_layer_shell_v1 *layer_shell;
static struct wl_display *display;
static struct wl_surface *surface;
static struct zwlr_layer_surface_v1 *layer_surface;
static struct wl_buffer *buffer;
static char **child_argv;
static uint32_t dim_pixel;
static uint32_t buffer_width;
static uint32_t buffer_height;
static int launched;
static int lock_fd = -1;
static pid_t child_pid;
static volatile sig_atomic_t dismissed;

/* The tree of a busy desktop is tens of kilobytes, not megabytes. */
static char sway_json[1 << 20];

/* Only one dimmer may own the screen at a time. A repeated shortcut dismisses
 * the launcher of the lock holder. It does not stack another surface. */
static int claim_screen(void)
{
	const char *runtime = getenv("XDG_RUNTIME_DIR");
	char path[256];
	char pid[32];
	int len;

	snprintf(path, sizeof path, "%s/launcher-dim.lock",
		 runtime != NULL ? runtime : "/tmp");
	lock_fd = open(path, O_RDWR | O_CREAT | O_CLOEXEC, 0600);
	if (lock_fd < 0) {
		perror("open lock");
		return 0;
	}
	if (flock(lock_fd, LOCK_EX | LOCK_NB) < 0) {
		if (errno == EWOULDBLOCK)
			return 0;
		perror("flock");
		return 0;
	}

	len = snprintf(pid, sizeof pid, "%ld\n", (long)getpid());
	if (ftruncate(lock_fd, 0) < 0 || pwrite(lock_fd, pid, len, 0) != len)
		perror("write lock");
	return 1;
}

/* The lock file contains the PID of the holder. A second press uses the PID
 * to tell the holder to close its launcher. */
static void dismiss_holder(void)
{
	char buf[32];
	ssize_t n = pread(lock_fd, buf, sizeof buf - 1, 0);

	if (n <= 0)
		return;
	buf[n] = '\0';
	pid_t pid = (pid_t)strtol(buf, NULL, 10);
	if (pid > 0)
		kill(pid, SIGUSR1);
}

static void on_dismiss(int sig)
{
	(void)sig;
	dismissed = 1;
	if (child_pid > 0)
		kill(child_pid, SIGTERM);
}

static void registry_global(void *data, struct wl_registry *registry, uint32_t name,
			    const char *interface, uint32_t version)
{
	(void)data;
	(void)version;
	if (strcmp(interface, wl_compositor_interface.name) == 0) {
		compositor = wl_registry_bind(registry, name,
					      &wl_compositor_interface, 4);
	} else if (strcmp(interface, wl_shm_interface.name) == 0) {
		shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
	} else if (strcmp(interface, zwlr_layer_shell_v1_interface.name) == 0) {
		layer_shell = wl_registry_bind(registry, name,
					       &zwlr_layer_shell_v1_interface, 1);
	}
}

static void registry_global_remove(void *data, struct wl_registry *registry,
				   uint32_t name)
{
	(void)data;
	(void)registry;
	(void)name;
}

static const struct wl_registry_listener registry_listener = {
	.global = registry_global,
	.global_remove = registry_global_remove,
};

static uint32_t argb(uint8_t r, uint8_t g, uint8_t b, uint8_t a)
{
	return ((uint32_t)a << 24) | ((uint32_t)(r * a / 255) << 16) |
	       ((uint32_t)(g * a / 255) << 8) | (uint32_t)(b * a / 255);
}

/* Build the sheet but keep it off screen: the launcher decides when it maps. */
static void prepare_sheet(uint32_t width, uint32_t height)
{
	int stride = (int)width * 4;
	int size = stride * (int)height;
	char name[32];
	int fd;

	snprintf(name, sizeof name, "launcher-dim-%d", getpid());
	fd = memfd_create(name, MFD_CLOEXEC);
	if (fd < 0) {
		perror("memfd_create");
		exit(1);
	}
	if (ftruncate(fd, size) < 0) {
		perror("ftruncate");
		exit(1);
	}
	uint32_t *data = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (data == MAP_FAILED) {
		perror("mmap");
		exit(1);
	}
	for (int i = 0; i < size / 4; i++)
		data[i] = dim_pixel;

	struct wl_shm_pool *pool = wl_shm_create_pool(shm, fd, size);
	buffer = wl_shm_pool_create_buffer(pool, 0, width, height, stride,
					   WL_SHM_FORMAT_ARGB8888);
	wl_shm_pool_destroy(pool);
	close(fd);
	buffer_width = width;
	buffer_height = height;
}

static void show_sheet(void)
{
	wl_surface_attach(surface, buffer, 0, 0);
	wl_surface_damage_buffer(surface, 0, 0, (int32_t)buffer_width,
				 (int32_t)buffer_height);
	wl_surface_commit(surface);
	/* Nothing else runs on this display until the launcher exits. */
	wl_display_flush(display);
}

static int write_full(int fd, const void *buf, size_t len)
{
	const char *p = buf;

	while (len > 0) {
		ssize_t n = write(fd, p, len);

		if (n < 0) {
			if (errno == EINTR)
				continue;
			return 0;
		}
		p += n;
		len -= (size_t)n;
	}
	return 1;
}

static int read_full(int fd, void *buf, size_t len)
{
	char *p = buf;

	while (len > 0) {
		ssize_t n = read(fd, p, len);

		if (n <= 0) {
			if (n == 0)
				return 0;
			if (errno == EINTR)
				continue;
			return 0;
		}
		p += n;
		len -= (size_t)n;
	}
	return 1;
}

static int sway_connect(void)
{
	const char *path = getenv("SWAYSOCK");
	struct sockaddr_un addr;
	int fd;

	if (path == NULL || *path == '\0' || strlen(path) >= sizeof addr.sun_path)
		return -1;
	fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
	if (fd < 0)
		return -1;
	memset(&addr, 0, sizeof addr);
	addr.sun_family = AF_UNIX;
	memcpy(addr.sun_path, path, strlen(path) + 1);
	if (connect(fd, (struct sockaddr *)&addr, sizeof addr) < 0) {
		close(fd);
		return -1;
	}
	return fd;
}

/* sway's IPC replies carry a 14-byte header: "i3-ipc", length, type. */
static int sway_get_tree(int fd, size_t *len)
{
	static const char magic[6] = { 'i', '3', '-', 'i', 'p', 'c' };
	uint32_t zero = 0;
	uint32_t type = 4;
	char header[14];
	uint32_t size;

	memcpy(header, magic, 6);
	memcpy(header + 6, &zero, 4);
	memcpy(header + 10, &type, 4);
	if (!write_full(fd, header, sizeof header) ||
	    !read_full(fd, header, sizeof header) ||
	    memcmp(header, magic, 6) != 0)
		return 0;
	memcpy(&size, header + 6, 4);
	if (size >= sizeof sway_json || !read_full(fd, sway_json, size))
		return 0;
	sway_json[size] = '\0';
	*len = size;
	return 1;
}

struct layer_scan {
	const char *cursor;
	const char *end;
	const char *array_end;
};

/* The layer surface list swayfx adds to every output of its IPC tree. */
static const char layer_array_key[] = "\"layer_shell_surfaces\"";

/* Finds the value of `key` in [from, limit), tolerating the whitespace json-c
 * puts around the colon and after commas. */
static const char *find_value(const char *from, const char *limit,
			      const char *key, size_t key_len)
{
	const char *p = from;

	while ((p = memmem(p, (size_t)(limit - p), key, key_len)) != NULL) {
		const char *q = p + key_len;

		while (q < limit && (*q == ' ' || *q == '\t' || *q == '\n' ||
				     *q == '\r'))
			q++;
		if (q < limit && *q == ':') {
			q++;
			while (q < limit && (*q == ' ' || *q == '\t' ||
					     *q == '\n' || *q == '\r'))
				q++;
			return q;
		}
		p += key_len;
	}
	return NULL;
}

/* Steps to the next mapped layer surface of the tree and returns its
 * namespace. swayfx describes each surface of an output as
 *   "layer_shell_surfaces": [ { "namespace": "waybar", "layer": "top",
 *   "extent": { "width": 1920, "height": 24, "x": 0, "y": 0 }, ... } ]
 * and the extent is only non-zero once the surface is mapped. */
static int next_mapped_layer(struct layer_scan *scan, const char **name,
			     size_t *name_len)
{
	static const char namespace_key[] = "\"namespace\"";
	static const char width_key[] = "\"width\"";
	static const char height_key[] = "\"height\"";

	for (;;) {
		const char *entry;
		const char *name_start;
		const char *name_end;
		const char *width_at;
		const char *height_at;

		if (scan->array_end == NULL) {
			const char *found;

			if (scan->cursor == scan->end)
				return 0;
			found = find_value(scan->cursor, scan->end,
					   layer_array_key,
					   sizeof layer_array_key - 1);
			if (found == NULL || found == scan->end ||
			    *found != '[') {
				scan->cursor = scan->end;
				return 0;
			}
			scan->cursor = found + 1;
			scan->array_end = memchr(scan->cursor, ']',
						 (size_t)(scan->end - scan->cursor));
			if (scan->array_end == NULL) {
				scan->cursor = scan->end;
				return 0;
			}
		}

		entry = find_value(scan->cursor,
				   scan->array_end, namespace_key,
				   sizeof namespace_key - 1);
		if (entry == NULL) {
			scan->cursor = scan->array_end + 1;
			scan->array_end = NULL;
			continue;
		}
		if (entry == scan->array_end || *entry != '"') {
			scan->cursor = entry + 1;
			continue;
		}
		name_start = entry + 1;
		name_end = memchr(name_start, '"',
				  (size_t)(scan->array_end - name_start));
		if (name_end == NULL) {
			scan->cursor = scan->array_end + 1;
			scan->array_end = NULL;
			continue;
		}
		scan->cursor = name_end + 1;
		*name = name_start;
		*name_len = (size_t)(name_end - name_start);
		width_at = find_value(name_end, scan->array_end, width_key,
				      sizeof width_key - 1);
		height_at = find_value(name_end, scan->array_end, height_key,
				       sizeof height_key - 1);
		if (width_at == NULL || height_at == NULL)
			continue;
		if (strtol(width_at, NULL, 10) > 0 &&
		    strtol(height_at, NULL, 10) > 0)
			return 1;
	}
}

/* Records the namespaces that are already on screen, one per line. The sheet
 * itself is still unmapped at this point, so it is not part of the list.
 * Returns 0 when the tree has no layer surface list at all: a compositor that
 * does not report one keeps the immediate commit instead of waiting for a
 * surface that will never appear there. */
static int snapshot_layers(const char *json, size_t len, char *out, size_t cap)
{
	struct layer_scan scan = { .cursor = json, .end = json + len };
	const char *name;
	size_t name_len;
	size_t used = 0;

	out[0] = '\0';
	if (memmem(json, len, layer_array_key, sizeof layer_array_key - 1) == NULL)
		return 0;
	while (next_mapped_layer(&scan, &name, &name_len)) {
		if (used + name_len + 1 >= cap)
			break;
		memcpy(out + used, name, name_len);
		used += name_len;
		out[used++] = '\n';
		out[used] = '\0';
	}
	return 1;
}

static int listed(const char *names, const char *name, size_t name_len)
{
	const char *line = names;

	while (*line != '\0') {
		size_t len = strcspn(line, "\n");

		if (len == name_len && memcmp(line, name, name_len) == 0)
			return 1;
		line += len;
		if (*line == '\n')
			line++;
	}
	return 0;
}

/* The launcher is the first layer surface to appear that was not already
 * mapped when the helper started. */
static int has_new_layer(const char *json, size_t len, const char *baseline)
{
	struct layer_scan scan = { .cursor = json, .end = json + len };
	const char *name;
	size_t name_len;

	while (next_mapped_layer(&scan, &name, &name_len)) {
		if (!listed(baseline, name, name_len))
			return 1;
	}
	return 0;
}

/* Returns 1 when the sheet belongs on screen: the launcher mapped, sway IPC
 * failed, or the launcher is taking too long. Returns 0 when there is nothing
 * to dim because the launcher exited or the shortcut was pressed again. */
static int wait_for_launcher(int fd, const char *baseline)
{
	struct timespec start;
	struct timespec now;
	struct timespec pause = { .tv_nsec = LAUNCHER_POLL_NS };

	clock_gettime(CLOCK_MONOTONIC, &start);
	for (;;) {
		size_t len;

		if (!sway_get_tree(fd, &len))
			return 1;
		if (has_new_layer(sway_json, len, baseline))
			return 1;
		if (dismissed)
			return 0;
		if (child_pid > 0) {
			int status;

			if (waitpid(child_pid, &status, WNOHANG) == child_pid)
				child_pid = 0;
		}
		if (child_pid == 0)
			return 0;
		clock_gettime(CLOCK_MONOTONIC, &now);
		if ((now.tv_sec - start.tv_sec) * 1000L +
			    (now.tv_nsec - start.tv_nsec) / 1000000L >=
		    LAUNCHER_MAP_TIMEOUT_MS)
			return 1;
		nanosleep(&pause, NULL);
	}
}

static void wait_for_child(void)
{
	int status;

	if (child_pid == 0)
		return;
	if (dismissed)
		kill(child_pid, SIGTERM);
	for (;;) {
		pid_t reaped = waitpid(child_pid, &status, 0);

		if (reaped == child_pid)
			break;
		if (reaped < 0 && errno != EINTR)
			break;
		if (dismissed)
			kill(child_pid, SIGTERM);
	}
}

static void configure(void *data, struct zwlr_layer_surface_v1 *ls,
		      uint32_t serial, uint32_t width, uint32_t height)
{
	(void)data;
	zwlr_layer_surface_v1_ack_configure(ls, serial);
	if (dismissed)
		exit(0);
	if (launched)
		return;
	launched = 1;

	/* Take the baseline before the fork: a launcher that maps before the
	 * first poll would otherwise already be part of it. */
	int sway_fd = sway_connect();
	char baseline[1024] = "";
	int baseline_known = 0;
	size_t len;

	if (sway_fd >= 0 && sway_get_tree(sway_fd, &len) &&
	    snapshot_layers(sway_json, len, baseline, sizeof baseline))
		baseline_known = 1;

	child_pid = fork();
	if (child_pid == 0) {
		struct sigaction dfl;

		memset(&dfl, 0, sizeof dfl);
		dfl.sa_handler = SIG_DFL;
		sigaction(SIGUSR1, &dfl, NULL);
		execvp(child_argv[0], child_argv);
		_exit(127);
	}
	if (child_pid < 0) {
		perror("fork");
		exit(1);
	}

	prepare_sheet(width, height);
	if ((!baseline_known || wait_for_launcher(sway_fd, baseline)) &&
	    !dismissed)
		show_sheet();
	if (sway_fd >= 0)
		close(sway_fd);
	wait_for_child();
	exit(0);
}

static void closed(void *data, struct zwlr_layer_surface_v1 *ls)
{
	(void)data;
	(void)ls;
	exit(0);
}

static const struct zwlr_layer_surface_v1_listener layer_surface_listener = {
	.configure = configure,
	.closed = closed,
};

int main(int argc, char **argv)
{
	double r = 0, g = 0, b = 0, a = 0.35;

	if (argc < 3) {
		fprintf(stderr, "usage: %s RGBA COMMAND [ARG...]\n", argv[0]);
		return 2;
	}
	if (sscanf(argv[1], "rgba ( %lf , %lf , %lf , %lf )", &r, &g, &b, &a) != 4) {
		fprintf(stderr, "%s: expected rgba(r, g, b, a), got %s\n", argv[0],
			argv[1]);
		return 2;
	}
	child_argv = &argv[2];
	dim_pixel = argb((uint8_t)r, (uint8_t)g, (uint8_t)b,
			 (uint8_t)(a * 255 + 0.5));

	if (!claim_screen()) {
		dismiss_holder();
		return 0;
	}

	struct sigaction sa;

	memset(&sa, 0, sizeof sa);
	sa.sa_handler = on_dismiss;
	sigemptyset(&sa.sa_mask);
	sigaction(SIGUSR1, &sa, NULL);

	display = wl_display_connect(NULL);
	if (display == NULL) {
		fprintf(stderr, "%s: cannot connect to Wayland display\n", argv[0]);
		return 1;
	}
	struct wl_registry *registry = wl_display_get_registry(display);
	wl_registry_add_listener(registry, &registry_listener, NULL);
	wl_display_roundtrip(display);

	surface = wl_compositor_create_surface(compositor);
	layer_surface = zwlr_layer_shell_v1_get_layer_surface(
		layer_shell, surface, NULL, ZWLR_LAYER_SHELL_V1_LAYER_TOP, "dim");
	zwlr_layer_surface_v1_add_listener(layer_surface,
					   &layer_surface_listener, NULL);
	zwlr_layer_surface_v1_set_anchor(layer_surface,
					 ZWLR_LAYER_SURFACE_V1_ANCHOR_TOP |
						 ZWLR_LAYER_SURFACE_V1_ANCHOR_BOTTOM |
						 ZWLR_LAYER_SURFACE_V1_ANCHOR_LEFT |
						 ZWLR_LAYER_SURFACE_V1_ANCHOR_RIGHT);
	zwlr_layer_surface_v1_set_exclusive_zone(layer_surface, 0);
	zwlr_layer_surface_v1_set_keyboard_interactivity(layer_surface, 0);

	struct wl_region *empty = wl_compositor_create_region(compositor);
	wl_surface_set_input_region(surface, empty);
	wl_region_destroy(empty);
	wl_surface_commit(surface);

	while (wl_display_dispatch(display) != -1)
		;
	return 0;
}
