import csv
import sys

def path2port(file_path, file_out):
    PORTS = {}

    print(f"[*INFO*], [*file_path*], [{file_path}],")

    with open(file_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip the header row
            for row in reader:
                if len(row) >= 7:
                    portid1, portname1, portid2, portname2 = row[0], row[1], row[6], row[7]
                    portid1= int(portid1[4:])
                    portid2 = int(portid2[4:])

                    PORTS[portid1] = portname1
                    PORTS[portid2] = portname2

    PORTS = dict(sorted(PORTS.items(), key=lambda x: x[0]))  # Sort by port name

    print(f"[*INFO*], [*file_out*], [{file_out}],")
    with open(file_out, 'w', newline='') as out:
        for portid, portname in PORTS.items():
            print(f"{portid}: {portname}")
            csv.writer(out).writerow([portid, portname])

if __name__ == "__main__":
    path2port(sys.argv[1], sys.argv[2])