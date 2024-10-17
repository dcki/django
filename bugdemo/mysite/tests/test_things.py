from django.test import SimpleTestCase


class AlwaysFailTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        try:
            raise Exception('Intentional error')
        except:
            super().tearDownClass()
            raise

    def test_should_pass_a(self) -> None:
        pass

    def test_should_pass_b(self) -> None:
        pass


# Exists so that, when an attempt is made to run tests in parallel, and at
# least two TestCases are specified, then tests actually run in parallel.
# (As of this writing, Django runs tests serially if there is only one test
# suite to run, even if `--parallel=2` is specified.)
class AlwaysPassTest(SimpleTestCase):
    def test_should_pass_a(self) -> None:
        pass

    def test_should_pass_b(self) -> None:
        pass
