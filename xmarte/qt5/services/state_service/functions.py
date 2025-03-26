''' The storage of generic functions used in the State Service across multiple modules '''
from martepy.marte2.objects import MARTe2ConfigurationDatabase, MARTe2Message

def genNextStateMsgs(state_name, app_name):
    ''' Generates the State Message for the next state '''
    params = MARTe2ConfigurationDatabase(objects = {"param1": state_name})
    prepare = MARTe2Message(f"+PrepareChangeTo{state_name}Msg", app_name,
                            "PrepareNextState", params)
    defaultmessages = [MARTe2Message("+StopCurrentStateExecutionMsg",
                                     app_name, "StopCurrentStateExecution"),
                        prepare,
                        MARTe2Message("+StartNextStateExecutionMsg",
                                      app_name, "StartNextStateExecution")]
    return defaultmessages
