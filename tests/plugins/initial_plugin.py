# https://stackoverflow.com/a/35394239/6597765


def pytest_configure(config):
    print("Start pytest, configure")


def pytest_unconfigure(config):
    print("End pytest, unconfigure")
