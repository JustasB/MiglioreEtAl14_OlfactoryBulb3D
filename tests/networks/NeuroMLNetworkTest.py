import os, sys, re, json
from matplotlib import pyplot as plt
import numpy as np
sys.path.insert(0,'..')
from tests.ModelTest import ModelTest
from tests.networks.NEURONNetworkTest import NEURONNetworkTest

class NeuroMLNetworkTest(ModelTest):
    def getResults(self):

        # Gather info from network nml file to generate the test bed
        with open(self.path) as f:
            networkNML = f.read()
            networkID = re.compile('<network.*id="(.*?)"').search(networkNML).group(1)

        # Create a test bed for channel
        with open("networks/LEMS_TestBed_Template.xml") as f:
            testBed = f.read()

        testBed = testBed \
            .replace("[NetworkFile]", self.modelFileName()) \
            .replace("[NetworkID]", networkID)

        testBedFile = self.modelFileName() + "_TestBed.xml"

        # Place the lems test bed in same folder as the channel
        with open(self.modelDir() + "/" + testBedFile, "w") as f:
            f.write(testBed)

        # Convert NML to NEURON
        os.chdir(self.modelDir())
        self.printAndRun("jnml " + testBedFile + " -neuron")

        # Return cwd to starting dir
        self.restoreStartDir()

        # Once converted to NEURON, create sub model
        subModel = NEURONNetworkTest()
        subModel.path = self.modelDir() + "/" + networkID + ".hoc"
        subModel.label = self.label
        subModel.prepare = self.prepare
        subModel.currentRange = self.currentRange
        subModel.resultsFile = self.resultsFile

        # Now the converted mod file is ready for the protocol
        subModel.getResults()