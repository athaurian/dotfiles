/* Full-screen dim sheet behind a launcher command on X11.
 *
 * The Wayland helper asks the compositor for a layer surface. X11 has no
 * layers, so the sheet is an override-redirect ARGB window stacked above the
 * managed windows. The dock struts are left clear so the bar stays readable,
 * as the bar would sit above the layer surface on Wayland.
 *
 * Rofi paints its window before it maps it, about 70 ms after the exec. A
 * sheet mapped before the fork is therefore already on screen on its own when
 * the launcher arrives. The sheet waits for the launcher's map instead and
 * goes directly below it, so both reach the compositor in the same frame.
 *
 * Compositing is mandatory. Without a compositor a 32-bit window is an opaque
 * black rectangle, so the launcher runs undimmed instead.
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
#include <sys/select.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include <X11/Xatom.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/shape.h>

static Display *display;
static Window sheet;
static Atom type_atom;
static Atom dock_atom;
static Atom strut_atom;
static Atom strut_partial_atom;
static Atom pid_atom;
static char **child_argv;
static unsigned long dim_pixel;
static int lock_fd = -1;
static pid_t child_pid;
static volatile sig_atomic_t dismissed;

/* Only one dimmer may own the screen at a time. A repeated shortcut dismisses
 * the launcher of the lock holder. It does not stack another sheet. */
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

static unsigned long argb(uint8_t r, uint8_t g, uint8_t b, uint8_t a)
{
	return ((unsigned long)a << 24) | ((unsigned long)(r * a / 255) << 16) |
	       ((unsigned long)(g * a / 255) << 8) | (unsigned long)(b * a / 255);
}

static int composited(void)
{
	char name[32];

	snprintf(name, sizeof name, "_NET_WM_CM_S%d", DefaultScreen(display));
	return XGetSelectionOwner(display, XInternAtom(display, name, False)) !=
	       None;
}

static int read_edges(Window window, Atom property, long *edges)
{
	unsigned char *data = NULL;
	unsigned long count = 0;
	unsigned long after = 0;
	Atom type;
	int format;

	if (XGetWindowProperty(display, window, property, 0, 4, False, XA_CARDINAL,
			       &type, &format, &count, &after, &data) != Success)
		return 0;
	if (data != NULL && format == 32 && count >= 4) {
		for (int i = 0; i < 4; i++)
			edges[i] = ((long *)data)[i];
		XFree(data);
		return 1;
	}
	if (data != NULL)
		XFree(data);
	return 0;
}

static void add_struts(Window window, long *edges)
{
	long values[4];

	if (!read_edges(window, strut_partial_atom, values) &&
	    !read_edges(window, strut_atom, values))
		return;
	for (int i = 0; i < 4; i++) {
		if (values[i] > edges[i])
			edges[i] = values[i];
	}
}

/* i3 does not implement _NET_WORKAREA, so collect the reserved edges from the
 * docks instead. It keeps every client inside a frame window, so a dock is one
 * level below the root child. */
static void reserve_struts(long *edges)
{
	Window root = DefaultRootWindow(display);
	Window root_return;
	Window parent;
	Window *children = NULL;
	unsigned int count = 0;

	for (int i = 0; i < 4; i++)
		edges[i] = 0;
	if (!XQueryTree(display, root, &root_return, &parent, &children, &count))
		return;
	for (unsigned int i = 0; i < count; i++) {
		Window kid_root;
		Window kid_parent;
		Window *kids = NULL;
		unsigned int kid_count = 0;

		add_struts(children[i], edges);
		if (!XQueryTree(display, children[i], &kid_root, &kid_parent, &kids,
				&kid_count))
			continue;
		for (unsigned int j = 0; j < kid_count; j++)
			add_struts(kids[j], edges);
		if (kids != NULL)
			XFree(kids);
	}
	if (children != NULL)
		XFree(children);
}

static int create_sheet(void)
{
	int screen = DefaultScreen(display);
	int screen_width = DisplayWidth(display, screen);
	int screen_height = DisplayHeight(display, screen);
	XVisualInfo vinfo;
	XSetWindowAttributes attrs;
	Colormap colormap;
	int shape_event;
	int shape_error;
	long edges[4];
	int x;
	int y;
	int width;
	int height;

	if (!XShapeQueryExtension(display, &shape_event, &shape_error))
		return 0;
	if (!XMatchVisualInfo(display, screen, 32, TrueColor, &vinfo))
		return 0;

	reserve_struts(edges);
	x = (int)edges[0];
	y = (int)edges[2];
	width = screen_width - (int)edges[0] - (int)edges[1];
	height = screen_height - (int)edges[2] - (int)edges[3];
	if (width < 1 || height < 1) {
		x = 0;
		y = 0;
		width = screen_width;
		height = screen_height;
	}

	colormap = XCreateColormap(display, RootWindow(display, screen),
				   vinfo.visual, AllocNone);
	memset(&attrs, 0, sizeof attrs);
	attrs.override_redirect = True;
	attrs.background_pixel = dim_pixel;
	attrs.border_pixel = 0;
	attrs.colormap = colormap;
	sheet = XCreateWindow(display, RootWindow(display, screen), x, y, width,
			      height, 0, vinfo.depth, InputOutput, vinfo.visual,
			      CWOverrideRedirect | CWBackPixel | CWBorderPixel |
				      CWColormap,
			      &attrs);
	if (sheet == None)
		return 0;
	XChangeProperty(display, sheet, type_atom, XA_ATOM, 32, PropModeReplace,
			(unsigned char *)&dock_atom, 1);
	/* Input reaches the window underneath, as on the layer surface. */
	XShapeCombineRectangles(display, sheet, ShapeInput, 0, 0, NULL, 0, ShapeSet,
				Unsorted);
	return 1;
}

static pid_t window_pid(Window window)
{
	Atom type;
	int format;
	unsigned long count = 0;
	unsigned long after = 0;
	unsigned char *data = NULL;
	pid_t pid = 0;

	if (XGetWindowProperty(display, window, pid_atom, 0, 1, False, XA_CARDINAL,
			       &type, &format, &count, &after, &data) != Success)
		return 0;
	if (data != NULL) {
		if (format == 32 && count >= 1)
			pid = (pid_t)((long *)data)[0];
		XFree(data);
	}
	return pid;
}

/* _NET_WM_PID names the launcher, but a wrapper such as timeout sits between
 * the helper and the launcher, so walk the parents up to the child we started. */
static int from_child(pid_t pid)
{
	char path[64];
	char buf[512];

	for (int depth = 0; pid > 0 && depth < 8; depth++) {
		FILE *stat;
		char *end;
		long parent;

		if (pid == child_pid)
			return 1;
		snprintf(path, sizeof path, "/proc/%ld/stat", (long)pid);
		stat = fopen(path, "r");
		if (stat == NULL)
			return 0;
		if (fgets(buf, sizeof buf, stat) == NULL) {
			fclose(stat);
			return 0;
		}
		fclose(stat);
		end = strrchr(buf, ')');
		if (end == NULL || sscanf(end + 2, "%*c %ld", &parent) != 1)
			return 0;
		pid = (pid_t)parent;
	}
	return 0;
}

/* Returns the first window the launcher maps, or None when it exits first or
 * does not map within the timeout. A slow launcher keeps the old behaviour:
 * the sheet is mapped after the wait and the launcher maps above it. */
static Window wait_for_launcher(void)
{
	int fd = ConnectionNumber(display);
	struct timespec start;

	clock_gettime(CLOCK_MONOTONIC, &start);
	for (;;) {
		struct timespec now;
		struct timeval timeout;
		fd_set ready;
		XEvent event;
		long remaining;

		if (child_pid == 0 || dismissed)
			return None;
		clock_gettime(CLOCK_MONOTONIC, &now);
		remaining = 300 - ((now.tv_sec - start.tv_sec) * 1000L +
				   (now.tv_nsec - start.tv_nsec) / 1000000L);
		if (remaining <= 0)
			return None;
		if (remaining > 20)
			remaining = 20;
		timeout.tv_sec = 0;
		timeout.tv_usec = remaining * 1000L;
		FD_ZERO(&ready);
		FD_SET(fd, &ready);
		if (select(fd + 1, &ready, NULL, NULL, &timeout) == 0) {
			int status;

			if (waitpid(child_pid, &status, WNOHANG) == child_pid)
				child_pid = 0;
			continue;
		}
		while (XPending(display) > 0) {
			XNextEvent(display, &event);
			if (event.type == MapNotify &&
			    from_child(window_pid(event.xmap.window)))
				return event.xmap.window;
		}
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

	display = XOpenDisplay(NULL);
	if (display == NULL) {
		fprintf(stderr, "%s: cannot open X display\n", argv[0]);
		return 1;
	}
	type_atom = XInternAtom(display, "_NET_WM_WINDOW_TYPE", False);
	dock_atom = XInternAtom(display, "_NET_WM_WINDOW_TYPE_DOCK", False);
	strut_atom = XInternAtom(display, "_NET_WM_STRUT", False);
	strut_partial_atom = XInternAtom(display, "_NET_WM_STRUT_PARTIAL", False);
	pid_atom = XInternAtom(display, "_NET_WM_PID", False);

	if (!composited() || !create_sheet()) {
		XCloseDisplay(display);
		execvp(child_argv[0], child_argv);
		perror("execvp");
		_exit(127);
	}

	/* Subscribe before the fork, or a fast launcher maps before the
	 * subscription exists and the sheet waits for the whole timeout. */
	XSelectInput(display, DefaultRootWindow(display), SubstructureNotifyMask);
	XSync(display, False);

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
		Window launcher = wait_for_launcher();

		if (!dismissed && launcher != None) {
			XWindowChanges stack;

			/* Stacking the unmapped sheet below the launcher keeps it
			 * there when it is mapped, so the two are composited as
			 * one frame. */
			stack.sibling = launcher;
			stack.stack_mode = Below;
			XConfigureWindow(display, sheet, CWSibling | CWStackMode,
					 &stack);
			XMapWindow(display, sheet);
			XSync(display, False);
		} else if (child_pid != 0 && !dismissed) {
			XMapRaised(display, sheet);
			XSync(display, False);
		}
		wait_for_child();
	}
	XCloseDisplay(display);
	return 0;
}
