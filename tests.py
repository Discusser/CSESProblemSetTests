import subprocess
import zipfile
import os
import sys


def help():
    print("Usage:", sys.argv[0], "[taskNumber] [executablePath]")
    print(
        "The tests are read from tests/<taskNumber>/, and the tests directory should be in the same directory as this executable"
    )
    print(
        'If the tests/<taskNumber>/ directory is empty, no tests will be run. If the directory contains only a file named "<taskNumber>.zip", it will be extracted. If the directory already contains several files with `in` and `out` file extensions, those will be used for the tests'
    )


def getInOutFiles(dir) -> tuple[list[str], list[str]]:
    inFiles = []
    outFiles = []
    for file in os.listdir(dir):
        filePath = os.path.join(dir, file)
        if os.path.isfile(filePath):
            extension = file.split(".")[-1]
            if extension == "in":
                inFiles.append(filePath)
            elif extension == "out":
                outFiles.append(filePath)
    if len(inFiles) != len(outFiles):
        print(
            f"There are {len(inFiles)} '.in' files but {len(outFiles)} '.out' files. There should be the same amount of both."
        )
    return (inFiles, outFiles)


def main():
    if len(sys.argv) != 3:
        help()
        exit(-1)

    taskNumber = sys.argv[1]
    executablePath = sys.argv[2]

    selfDir = os.path.dirname(__file__)
    testDir = os.path.join(selfDir, "tests", taskNumber)
    inFiles, outFiles = getInOutFiles(testDir)

    if len(inFiles) == 0 or len(outFiles) == 0:
        zipPath = os.path.join(testDir, taskNumber + ".zip")
        if os.path.exists(zipPath):
            with zipfile.ZipFile(zipPath, "r") as zipFile:
                zipFile.extractall(testDir)
                inFiles, outFiles = getInOutFiles(testDir)
                print(
                    f"Extracted {os.path.basename(zipPath)}. There are now {len(inFiles)} test cases"
                )
    print(f"Running {len(inFiles)} test cases")

    for i in range(1, len(inFiles) + 1):
        inPath = os.path.join(testDir, str(i) + ".in")
        outPath = os.path.join(testDir, str(i) + ".out")
        inFile = open(inPath)
        outFile = open(outPath)
        proc = subprocess.Popen(
            executablePath,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        while proc.poll() is None:
            proc.stdin.writelines(inFile)
            proc.stdin.flush()
            out = proc.stdout.readlines()
            for k in range(len(out)):
                out[k] = out[k].strip()
            proc.terminate()

        outLines = sum(1 for _ in open(outPath))
        if len(out) != outLines:
            print(
                f"Test case #{str(i).ljust(3, ' ')} failed. Expected {outLines} lines of output, but found {out} instead"
            )
        else:
            failed = False
            for j in range(outLines):
                expectedLine = outFile.readline().strip()
                if out[j] != expectedLine:
                    failed = True
                    outDiff = ["\033[92m"]
                    prevWasWrong = False
                    for k, c in enumerate(out[j]):
                        if k >= len(expectedLine):
                            break
                        if c != expectedLine[k] and not prevWasWrong:
                            outDiff += "\033[91m"
                            prevWasWrong = True
                        elif c == expectedLine[k] and prevWasWrong:
                            outDiff += "\033[92m"
                            prevWasWrong = False
                        outDiff += c
                    outDiff += "\033[00m"
                    outDiff = "".join(outDiff)
                    print(f"  Test case #{str(i).ljust(3, ' ')} \033[91mfailed\033[00m")
                    print(f"    \033[96mExpected\033[00m: {expectedLine}")
                    print(f"    \033[93mFound\033[00m: {outDiff}")
                    break

            if not failed:
                print(f"  Test case #{str(i).ljust(3, ' ')} \033[92mpassed\033[00m")

        inFile.close()
        outFile.close()


if __name__ == "__main__":
    main()
