static void err(int eval, const char *fmt, ...)
{
	va_list argp;
	va_start(argp, fmt);
	vfprintf(stderr, fmt, argp);
	fprintf(stderr, ": %s\n", strerror(errno));
	exit(eval);
}

static void errx(int eval, const char *fmt, ...)
{
	va_list argp;
	va_start(argp, fmt);
	vfprintf(stderr, fmt, argp);
	fprintf(stderr, "\n");
	exit(eval);
}
