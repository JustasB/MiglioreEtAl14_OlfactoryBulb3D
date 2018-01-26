import os, sys, re, json
from matplotlib import pyplot as plt
import numpy as np
sys.path.insert(0,'..');
from tests.NEURONTest import NEURONTest

class NEURONNetworkTest(NEURONTest):

    def getResults(self):

        os.chdir(self.modelDir())

        # Compile mod files
        self.printAndRun("nrnivmodl")

        # Start neuron and load mod files
        self.loadNEURONandModFiles()

        # Perform any model specific preparations
        net = self.prepare(self.h)

        # First inject current into MC and record GC
        result1 = self.performProtocol(
            inputCellLabel    = "MC",
            outputCellLabel   = "GC",
            currentRange = self.currentRangeMC,
            inputCell = net["mitral"],
            outputCell = net["granule"]
        )

        # Then inject current into GC and record MC
        result2 = self.performProtocol(
            inputCellLabel="GC",
            outputCellLabel="MC",
            currentRange=self.currentRangeGC,
            inputCell=net["granule"],
            outputCell=net["mitral"]
        )

        result = { "iclamp": result1 + result2 }

        # DEBUG
        # # Plot the voltage traces
        # for trace in result["iclamp"]:
        #     plt.plot(trace["time"], trace["voltage"], label=trace["label"])
        #
        # plt.legend()
        # plt.show()

        # Save the traces to json file for later comparison
        self.saveResults(result)

        # Return cwd to starting dir
        self.restoreStartDir()

    def performProtocol(self, inputCellLabel, outputCellLabel, currentRange, inputCell, outputCell):
        ic = self.h.IClamp(inputCell.soma(0.5))
        ic.delay = 50
        ic.dur = 100
        ic.amp = -65

        self.h.tstop = ic.delay + ic.dur + 50  # With extra 50ms at the end
        self.h.steps_per_ms = 16
        self.h.dt = 1.0 / self.h.steps_per_ms

        # Record time, voltage, and current
        self.setupRecorders(t=self.h._ref_t, v=outputCell.soma(0.5)._ref_v, i=ic._ref_i)

        # Create test levels
        icLevels = np.linspace(np.min(currentRange),
                               np.max(currentRange),
                               num=5)

        #DEBUG
        #icLevels = [np.max(currentRange)]

        result = []

        # Run simulations for each IClamp test level
        for level in icLevels:
            ic.amp = level

            self.h.run()

            # Gather output variables - subsample to once per ms
            t, v, i = self.subSampleTVI(self.h.steps_per_ms)

            self.on_run_complete()

            t = np.array(t)
            v = np.array(v)
            i = np.array(i)

            window = np.where(t > ic.delay) # Show the interesting part

            t = t[window].tolist()
            v = v[window].tolist()
            i = i[window].tolist()

            result.append({
                "label": outputCellLabel + " v with " + str(level) + " nA into " + inputCellLabel,
                "time": t,
                "voltage": v,
                "current": i,
            })

        # Remove the stim
        ic.amp = 0

        return result

    def compareTo(self, target):
        return self.compareTraces(
            target,
            resultKey = "iclamp",
            variable = "voltage"
        )