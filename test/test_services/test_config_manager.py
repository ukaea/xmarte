
from test.utilities import *

@pytest.fixture
def manager(mainwindow):
    manager = [srv for srv in mainwindow.services if srv.__class__.__name__ == 'ConfigManager']
    if not manager:
        assert False
    manager = manager[0]
    return manager

def test_gen_plugins(manager) -> None:
    if os.path.exists(plugins := os.path.join(os.getcwd(), 'xmarte', 'plugins.yml')):
        os.remove(plugins)

    manager._discoverPlugins()

    assert manager._validatePluginYaml(manager._readYaml(plugins))

def test_bad_plugins(manager) -> None:
    with open('error.yml', 'w', encoding='utf-8') as fhand:
        fhand.write(
            '''
            key1: value1
            key2
            key3: value3
            '''
        )
    fhand.close()
    assert manager._readYaml('error.yml') == {}
    os.remove('error.yml')

def test_bad_settings(manager) -> None:
    assert manager._validateSettingsYaml({'RemotePanel': {'temp_folder': 'test_settings'}})
    os.rmdir('test_settings')

def test_false_plugins(manager) -> None:
    assert not manager._validatePluginYaml({})

def test_false_settings(manager) -> None:
    with pytest.raises(KeyError):
        manager._validateSettingsYaml({})
