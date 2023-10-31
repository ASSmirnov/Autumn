from autumn.public import dm
from examples.umbrella.interfaces import IExecutor

def test_male():
    with dm.copy():
        dm.init_profiles("test_male")
        dm.start()
        executor = dm.get_instance(IExecutor)
        result = executor.execute()
        assert result == {"Alexey": 1,
                          "Vanya": 1, 
                          "Dima": 3, 
                          "Leonid": 3, 
                          "Kolya": 2, 
                          "Gena": 1, 
                          "Slava": 1}
        


def test_female():
    with dm.copy():
        dm.init_profiles("test_female")
        dm.start()
        executor = dm.get_instance(IExecutor)
        result = executor.execute()
        assert result == {"Luda": 2,
                          "Gretta": 2,
                          "Dasha": 1,
                          "Rita": 2,
                          "Sveta": 2,
                          "Tanya": 1} 