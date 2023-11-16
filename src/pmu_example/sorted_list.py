from bisect import bisect_left
import sys
import csv
#creates ascending order sorted list (no duplicates). inserts items in O(n)
class KeySortedList:
    def __init__(self, key=None,  keyfunc=lambda v: v):
        self._list = []
        self._keys = []
        self._keyfunc = keyfunc

    def insert(self, item):
        k = self._keyfunc(item)  # Get key.
        try:
            #won't add key if already exists
            self._keys.index(k)
        except:
            i = bisect_left(self._keys, k)  # Determine where to insert item.
            self._keys.insert(i, k)  # Insert key of item to keys list.
            self._list.insert(i, item)  # Insert the item itself in the corresponding place.

    def retrieve_last_n(self, n):
        return self._list[-n:]

    def print_pmu(self):
        counter = 1
        for pmu in self._list:
            print(str(counter) + " : " + str(pmu["sync"]) + " | " + "Magnitude: " + str(pmu["phasors"][0]["magnitude"]) + " | Phase_angle: " + str(pmu["phasors"][0]["angle"]))
            counter += 1

            #index starts at 1
    def print_recovered(self, indexes_only):
        for i in range(len(self._list)):
            pmu = self._list[i]
            #generated packet
            if pmu["stat"] == 9:
                if indexes_only:
                    print(str(i + 1) + " indexed packet was recoved")
                else:
                    print(str(pmu["sync"]) + " | " + "Magnitude: " + str(pmu["phasors"][0]["magnitude"]) + " | Phase_angle: " + str(pmu["phasors"][0]["angle"]))

    def write_to_csv(self, filename):
        headers = ["index", "magnitude", "phase_angle", "is_predicted", "received_at"]
        csv_obj = [headers]
        for i in range(len(self._list)):
            pmu = self._list[i]
            csv_obj.append(
                [
                 i,
                 pmu["phasors"][0]["magnitude"],
                 pmu["phasors"][0]["angle"],
                 pmu["stat"] == 9,
                 pmu["received_at"]])
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(csv_obj)

    #TODO
    def flush():
        print("flush the list here")

    def get_last_n(self, n):
        return self._list[-n:]
