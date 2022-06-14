from chinfuzz.core import fuzz
from chinstrap.tests import getContractInterface
            
owner = "tz1YtuZ4vhzzn7ssCt93Put8U9UJDdvCXci4"
alice = "tz1LFuHW4Z9zsCwg1cgGTKU12WZAs27ZD14v"

def ChinfuzzFuzzerTestOneInput(data):
    # convert data (bytes) to required data type using FuzzedDataProvider
    fdp = fuzz.FuzzedDataProvider(data)
    
    # we generate numbers of size `10000`
    data = fdp.ConsumeInt(10000)

    # we get the contract interface as we do in Chinstrap tests
    contract = getContractInterface("SampleContract")

    # we initialise the storate and call the entrypoint we would like to fuzz
    storage = {"owner": owner, "counter": 0}
    contract.increment(data).interpret(storage=storage, source=owner)