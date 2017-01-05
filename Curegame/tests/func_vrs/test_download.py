import os
import hashlib
import random
import shutil
import tempfile
import time
import unittest

from vrs.util.download import saveurl

class TestSaveURL(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.filename_orig = os.path.join(self.tempdir, "test.orig")
        self.filename_save = os.path.join(self.tempdir, "test.save")
        self.url = "file:///" + self.filename_orig
        f = open(self.filename_orig, 'wb')
        f.write(os.urandom(10*1024*1024))
        f.close()

    def tearDown(self):
        shutil.rmtree(self.tempdir)
    
    def test_saveurl_single(self):
        saveurl(self.url, self.filename_save, numthreads=1)
        assert self.md5(self.filename_orig) == self.md5(self.filename_save)
        
    def test_saveurl_multiple(self):
        saveurl(self.url, self.filename_save, numthreads=16)
        assert self.md5(self.filename_orig) == self.md5(self.filename_save)
        
    def test_saveurl_throttle(self):
        timestart = time.time()
        saveurl(self.url, self.filename_save, bandwidth=500, numthreads=1)
        finishtime = time.time() - timestart
        assert finishtime > 15 and finishtime < 25
        assert self.md5(self.filename_orig) == self.md5(self.filename_save)

    def test_saveurl_throttle_multiple(self):
        timestart = time.time()
        saveurl(self.url, self.filename_save, bandwidth=500, numthreads=16)
        finishtime = time.time() - timestart
        assert finishtime > 15 and finishtime < 25
        assert self.md5(self.filename_orig) == self.md5(self.filename_save)
        
    def test_saveurl_throttle_resume(self):
        self.make_resume_file(self.filename_orig, self.filename_save, truncate=True)
        assert os.path.isfile(self.filename_save)
        assert os.path.getsize(self.filename_save) < os.path.getsize(self.filename_orig)
        timestart = time.time()
        saveurl(self.url, self.filename_save, bandwidth=500, numthreads=1)
        finishtime = time.time() - timestart
        assert self.md5(self.filename_orig) == self.md5(self.filename_save)

    def test_saveurl_throttle_multiple_resume(self):
        self.make_resume_file(self.filename_orig, self.filename_save, truncate=True)
        assert os.path.isfile(self.filename_save)
        assert os.path.getsize(self.filename_save) < os.path.getsize(self.filename_orig)
        timestart = time.time()
        saveurl(self.url, self.filename_save, bandwidth=500, numthreads=16)
        finishtime = time.time() - timestart
        assert self.md5(self.filename_orig) == self.md5(self.filename_save)

    def test_saveurl_throttle_resume_larger(self):
        self.make_resume_file(self.filename_orig, self.filename_save, enlarge=True)
        assert os.path.isfile(self.filename_save)
        assert os.path.getsize(self.filename_save) > os.path.getsize(self.filename_orig)
        timestart = time.time()
        saveurl(self.url, self.filename_save, bandwidth=500, numthreads=1)
        finishtime = time.time() - timestart
        assert self.md5(self.filename_orig) == self.md5(self.filename_save)

    def test_saveurl_throttle_multiple_resume_larger(self):
        self.make_resume_file(self.filename_orig, self.filename_save, enlarge=True)
        assert os.path.isfile(self.filename_save)
        assert os.path.getsize(self.filename_save) > os.path.getsize(self.filename_orig)
        timestart = time.time()
        saveurl(self.url, self.filename_save, bandwidth=500, numthreads=16)
        finishtime = time.time() - timestart
        assert self.md5(self.filename_orig) == self.md5(self.filename_save)
        
    def test_saveurl_throttle_resume_complete(self):
        self.make_resume_file(self.filename_orig, self.filename_save)
        assert os.path.isfile(self.filename_save)
        assert os.path.getsize(self.filename_save) == os.path.getsize(self.filename_orig)
        timestart = time.time()
        saveurl(self.url, self.filename_save, bandwidth=500, numthreads=1)
        finishtime = time.time() - timestart
        assert self.md5(self.filename_orig) == self.md5(self.filename_save)

    def test_saveurl_throttle_multiple_resume_complete(self):
        self.make_resume_file(self.filename_orig, self.filename_save)
        assert os.path.isfile(self.filename_save)
        assert os.path.getsize(self.filename_save) == os.path.getsize(self.filename_orig)
        timestart = time.time()
        saveurl(self.url, self.filename_save, bandwidth=500, numthreads=16)
        finishtime = time.time() - timestart
        assert self.md5(self.filename_orig) == self.md5(self.filename_save)
        
    def make_resume_file(self, src, dst, truncate=False, enlarge=False):
        shutil.copyfile(src, dst)
        if truncate:
            open(dst, "ab").truncate(random.randint(0, os.path.getsize(dst)))
        if enlarge:
            open(dst, "ab").write(os.urandom(1*1024*1024))
                
    def md5(self, filename):
        return hashlib.md5(open(filename).read()).digest()

    
if __name__ == '__main__':
   logging.getLogger().setLevel(logging.DEBUG)
   logging.getLogger().addHandler(logging.StreamHandler())
   unittest.TestLoader().loadTestsFromTestCase(TestSaveURL).debug()
