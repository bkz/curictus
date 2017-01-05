import os
import time
import unittest

from vrs.client.ActivityConfig import GameConfig, TestConfig
from vrs.config.activities import HGT_TESTS, HGT_GAMES


class TestActivities(unittest.TestCase):
    def test_assessments(self):
        for name in HGT_TESTS:
            self.assertTrue(self.run_activity(name, is_test=True))
            
    def test_games(self):
        for name in HGT_GAMES:
            self.assertTrue(self.run_activity(name, is_test=False))
                    
    def run_activity(self, name, is_test=False):
        start = time.time()

        self.force_exit = False

        def is_down():
            if (time.time() - start) > 5.0:
                self.force_exit = True
            return self.force_exit

        from vrs import resetbutton
        resetbutton.is_down = is_down

        from vrs.config import Config
        config = Config(os.path.join(os.environ["CUREGAME_ROOT"], "config.cfg"))

        import vrs.locale
        i18n_path = os.path.join(os.environ["CUREGAME_ROOT"], "media/i18n")
        vrs.locale.load_translations(i18n_path, "vrs")
        vrs.locale.set_locale(config.SYSTEM_LOCALE)
        
        from vrs.client import manager
        if is_test:
            manager.runtest(config, name, 'test', 'test', TestConfig("en_US", {}))
            return self.force_exit
        else:
            manager.rungame(config, name, 'test', 'test', GameConfig("en_US", {}, {}))
            return self.force_exit


if __name__ == '__main__':
    unittest.TestLoader().loadTestsFromTestCase(TestActivities).debug()
