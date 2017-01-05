#include <io.h>
#include <sys/types.h>

typedef ptrdiff_t ssize_t;

static off_t ftello(FILE *stream)
{
	return (off_t)ftell(stream);
}

static int fseeko(FILE *stream, off_t offset, int whence)
{
	return fseek(stream, (long)(offset), whence);
}
