/* Full-screen dim layer behind a launcher command.
 *
 * Connects to Wayland directly instead of using a toolkit. GTK startup alone
 * costs about 60 ms. The launcher must appear as fast as fuzzel alone.
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
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <wayland-client.h>

#include "wlr-layer-shell-unstable-v1-client-protocol.h"

static struct wl_compositor *compositor;
static struct wl_shm *shm;
static struct zwlr_layer_shell_v1 *layer_shell;
static struct wl_display *display;
static struct wl_surface *surface;
static struct zwlr_layer_surface_v1 *layer_surface;
static char **child_argv;
static uint32_t dim_pixel;
static int launched;
static int lock_fd = -1;
static pid_t child_pid;
static volatile sig_atomic_t dismissed;

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

static void paint(uint32_t width, uint32_t height, uint32_t pixel)
{
	int stride = width * 4;
	int size = stride * height;
	char name[32];
	snprintf(name, sizeof name, "launcher-dim-%d", getpid());
	int fd = memfd_create(name, MFD_CLOEXEC);
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
	for (int i = 0; i < stride * (int)height / 4; i++)
		data[i] = pixel;

	struct wl_shm_pool *pool = wl_shm_create_pool(shm, fd, size);
	struct wl_buffer *buffer = wl_shm_pool_create_buffer(
		pool, 0, width, height, stride, WL_SHM_FORMAT_ARGB8888);
	wl_shm_pool_destroy(pool);
	close(fd);

	wl_surface_attach(surface, buffer, 0, 0);
	wl_surface_damage_buffer(surface, 0, 0, width, height);
	wl_surface_commit(surface);
	/* The launch below blocks the dispatch loop. Flush the commit. */
	wl_display_flush(display);
}

static void configure(void *data, struct zwlr_layer_surface_v1 *ls,
		      uint32_t serial, uint32_t width, uint32_t height)
{
	(void)data;
	zwlr_layer_surface_v1_ack_configure(ls, serial);
	if (dismissed)
		exit(0);
	paint(width, height, dim_pixel);
	if (launched)
		return;
	launched = 1;
	child_pid = fork();
	if (child_pid == 0) {
		struct sigaction dfl;

		memset(&dfl, 0, sizeof dfl);
		dfl.sa_handler = SIG_DFL;
		sigaction(SIGUSR1, &dfl, NULL);
		execvp(child_argv[0], child_argv);
		_exit(127);
	}
	if (child_pid > 0) {
		int status;

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
		child_pid = 0;
	}
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
