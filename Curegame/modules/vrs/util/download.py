##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##############################################################################

import os
import time
import logging
import urllib
import threading
import Queue

_log = logging.getLogger('download')

###########################################################################
# TokenBucket.
###########################################################################

class TokenBucket(object):
    """
    Token bucket control mechanism which provides a very simple interface for
    limiting resource usage in various scenarious. The bucket is initially
    created with a capacity of C tokens and a fill rate value R which adds a
    token the bucket over time (one token every 1/R second). To schedule
    resource usage of size N simply call the consume(N) method which will take
    care of waiting until the required amount tokens are available. The
    algorithm allows burst of up to C tokens but over the long run the
    troughput is limited to the constant rate R.
    """
    def __init__(self, capacity, fillrate):
        """
        Initialize token bucket with a maximum ``capacity`` and a ``fillrate``
        which specifies how many tokens are added per second to the bucket.
        """
        self.capacity, self.tokens = capacity, capacity
        self.fillrate = float(fillrate)
        self.timestamp = time.time()

    def consume(self, n):
        """
        Remove ``n`` tokens from the bucket. If the bucket contains enough
        tokens the call will return without stalling (burst) else block until
        the required amount of tokens have been generated and consumed. Returns
        True if tokens were consumed without stalling or False if a wait was
        required.
        """
        # Note: We can only fill the bucket to it's maximum capacity even if
        # the request needs more tokens than available so larger requests will
        # have to be completed in multiple runs trough this loop.
        if n <= self.tokens:
            self.tokens -= n
            return True

        while n > 0:
            if n >= self.tokens:
                n -= self.tokens
                self.tokens = 0
            else:
                self.tokens -= n
                n = 0

            expected_waittime = min(self.capacity, n) / self.fillrate
            if expected_waittime > 0:
                time.sleep(expected_waittime)

            now = time.time()
            new_tokens = (now - self.timestamp) * self.fillrate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.timestamp = now
        return False


###########################################################################
# DownloadRateLimiter.
###########################################################################

class DownloadRateLimiter():
    """
    Wrapper for TokenBucket for usage in bandwidth throttling scenarios.

    Example:

        Limit downloading 'foo.zip' to 150 kB/s (with a maximum burst of 512 kB).

        rate_limit = DownloadRateLimiter(150, 512)

        for chunk in http('http://cdn.domain.com/files.zip').read():
            target_file.write(chunk)
            rate_limit.checkpoint(len(chunk))

    """
    def __init__(self, rate, burst=None):
        """
        Create instance with ``rate`` specifying the average bandwidth limit in
        kB/s. ``burst`` may be optionally set to a kB value controlling the
        size of the token bucket otherwise it will default to ``rate`` (which
        is the best choice for most usage scenarios).
        """
        self.lock = threading.Lock()
        self.rate = float(rate)
        self.avgrate = 0
        self.samples = []
        self.timestart = time.time()
        self.timestamp = self.timestart
        if burst:
            self.bucket = TokenBucket(burst, rate)
        else:
            self.bucket = TokenBucket(rate, rate)

    def checkpoint(self, delta):
        """
        Report a checkpoint where ``delta`` bytes have been downloaded since
        the last the call, will possibly result in a sleep() for the calling
        thread if bandwidth throttling is needed.
        """
        self.lock.acquire()
        now = time.time()
        # Calculate size of downloaded data (in kB) and time spent since last
        # call, total so far and the total amount of data we expect to fetch.
        delta_kb = delta / 1024
        elapsed_time, delta_time = now - self.timestart, now - self.timestamp

        # Throttle bandwidth usage by consuming N tokens from our bucket
        # matching the amount of data transfered since last call. The bucket
        # will automatically sleep() the required throttle factor to control
        # the bandwidth usage.
        burst = self.bucket.consume(delta_kb)

        # Calculate average download rate (kB/s) by calculating a running mean
        # from a window of the 10 latest rate samples. Don't bother with
        # samples when transmission was temporarily allowed to burst during a
        # small period of time.
        if not burst:
            if delta_time > 0:
                self.samples.append(delta_kb / delta_time)
            if len(self.samples) > 10:
                self.samples = self.samples[-10:]
            if len(self.samples) > 0:
                self.avgrate = (0.9 * self.avgrate) + \
                               (0.1 * sum(self.samples) / len(self.samples))
                _log.debug("%.2f kB/s" % self.avgrate)

        # Update variables needed for calculating deltas in future calls.
        self.timestamp = now
        self.lock.release()


###########################################################################
# HTTP Download (with resume support)
###########################################################################

def urlsize(url):
    """
    Return the content size in bytes of the remote object ``url``.
    """
    request = urllib.FancyURLopener()
    webpage = request.open(url)
    size = 0
    try:
        size = int(webpage.headers["Content-Length"])
    except KeyError:
        pass
    webpage.close()
    return size


def saveurl(url, filename, bandwidth=None, resume=True, numthreads=8):
    """
    Download file located at ``url`` and save it to the fully qualified path
    ``filename``. Bandwidth throttling can optionally be enabled by setting
    ``bandwidth`` to a max limit in kB/s. If a partial download is detected
    we'll attempt to resume the download if possible unlesss ``resume`` is set
    to False in which case we'll re-downloaded the file. To speed up the
    download we'll pipeline HTTP request accross ``numthreads`` workers.
    Returns True/False to signal if download was successful or not.
    """
    timestart = time.time()
    totalsize = urlsize(url)
    if not totalsize:
        _log.debug("Could not determine size of %s" % url)
        return False
    if bandwidth:
        ratelimit = DownloadRateLimiter(bandwidth)
    else:
        ratelimit = None
    # Try to determine if we can resume a previous download or if we need
    # re-download file if local file is larger than the remote file.
    try:
        currentsize = os.path.getsize(filename)
        if currentsize > totalsize:
            currentsize = 0
    except os.error:
        currentsize = 0
    if resume and currentsize > 0:
        output = open(filename, "ab")
    else:
        output = open(filename, "wb")
    # We split the output file into chunks which are pipelined and downloaded
    # in parallell (assuming numthreads > 1). HTTP request for chunks (index,
    # offset, size) are scheduled as individual tasks which are then picked by
    # workers (threads). The downloaded data is placed into a priority queue
    # ordered by (index, data), so that we can retrieve chunks in parallell but
    # write them to disk in a serial fashion (1..N) in order to support resume.
    tasks = Queue.Queue()
    chunks = Queue.PriorityQueue()
    abort_event = threading.Event()

    def worker():
        while not abort_event.isSet():
            try:
                (index, offset, nbytes) = tasks.get(block=False)
                for retry in range(5):
                    try:
                        request = urllib.FancyURLopener()
                        if offset > 0:
                            request.addheader("Range","bytes=%s-" % offset)
                        page = request.open(url)
                        data = page.read(nbytes)
                        page.close()
                        chunks.put((index, data))
                        if ratelimit:
                            ratelimit.checkpoint(nbytes)
                        break # Chunk successfully feteched.
                    except Exception:
                        _log.exception("Exception in download worker")
                else:
                    raise RuntimeError("Failed to download %s:%s from %s" % (offset, nbytes, url))
            except Queue.Empty:
                break
            except Exception:
                _log.exception("Exception in download worker")
                abort_event.set()
                break

    if currentsize < totalsize:
        _log.info("Downloading %s (%s/%s bytes)" % (url, currentsize, totalsize))
        chunksize = 64*1024
        remaining = totalsize - currentsize
        chunkcount = remaining / chunksize
        leftover = remaining % chunksize
        for (index, k) in enumerate(range(chunkcount)):
            tasks.put((index, currentsize + k * chunksize, chunksize))
        if leftover > 0:
            tasks.put((chunkcount, remaining - leftover, leftover))
            chunkcount += 1
        workers = []
        for n in range(numthreads):
            t = threading.Thread(target=worker)
            workers.append(t)
            t.start()
        i = 0
        while i != chunkcount:
            if abort_event.isSet():
                _log.error("Worker failed, aborting download")
                break
            try:
                (index, data) = chunks.get(timeout=0.1)
                if i != index:
                    chunks.put((index, data)) # Put it back temporaily.
                else:
                    output.write(data)
                    i += 1
            except KeyboardInterrupt:
                _log.warning("Aborting download due to Ctrl+C")
                abort_event.set()
                break
            except Queue.Empty:
                pass
        for w in workers:
            w.join()

    output.close()

    if not abort_event.isSet():
        _log.info("Downloaded %s => %s in %.2f sec" % (url, filename, time.time() - timestart))
        return True
    else:
        return False


###########################################################################
# The End.
###########################################################################
