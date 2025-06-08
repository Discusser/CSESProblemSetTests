from io import TextIOWrapper
import subprocess
import psutil
import time
import zipfile
import os
import sys


TIME_LIMIT = 1.0  # seconds
MEMORY_LIMIT = 512.0  # megabytes
ANSI_RESET = "\033[00m"
ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_CYAN = "\033[96m"


def help():
    print("Usage:", sys.argv[0], "[taskNumber] [executablePath]")
    print(
        "The tests are read from tests/<taskNumber>/, and the tests directory should be in the same directory as this executable"
    )
    print(
        'If the tests/<taskNumber>/ directory is empty, no tests will be run. If the directory contains only a file named "<taskNumber>.zip", it will be extracted. If the directory already contains several files with `in` and `out` file extensions, those will be used for the tests'
    )


def getInOutFiles(dir: str) -> tuple[list[str], list[str]]:
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


def extractZip(file: str):
    print(file)
    if os.path.exists(file):
        with zipfile.ZipFile(file, "r") as f:
            f.extractall(os.path.dirname(file))


def getInOutFilesOrExtract(dir: str, filename: str) -> tuple[list[str], list[str]]:
    inFiles, outFiles = getInOutFiles(dir)
    if len(inFiles) == 0 or len(outFiles) == 0:
        extractZip(os.path.join(dir, filename))
        inFiles, outFiles = getInOutFiles(dir)
        print(f"Extracted {filename}")
    return inFiles, outFiles


def runProcess(path: str, stdin: TextIOWrapper):
    startTime = time.time()
    proc = subprocess.Popen(
        path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    psProc = psutil.Process(proc.pid)
    peakMemory = startMemory = psProc.memory_info().rss
    stdout = []
    while proc.poll() is None:
        proc.stdin.writelines(stdin)
        proc.stdin.flush()
        peakMemory = max(peakMemory, psProc.memory_info().rss)
        stdout = proc.stdout.readlines()
        proc.terminate()
    endTime = time.time()

    for i in range(len(stdout)):
        stdout[i] = stdout[i].strip()

    elapsedTime = endTime - startTime
    memoryUsage = (peakMemory - startMemory) / 1_000_000

    return stdout, elapsedTime, memoryUsage


def main():
    if len(sys.argv) != 3:
        help()
        exit(-1)

    taskNumber = sys.argv[1]
    executablePath = sys.argv[2]

    selfDir = os.path.dirname(__file__)
    testDir = os.path.join(selfDir, "tests", taskNumber)
    inFiles, outFiles = getInOutFilesOrExtract(testDir, taskNumber + ".zip")
    print(
        f"Running {len(inFiles)} test cases for problem {taskNumber}, '{os.path.basename(executablePath)}'"
    )

    for i in range(1, min(len(inFiles), len(outFiles)) + 1):
        inFilePath = os.path.join(testDir, str(i) + ".in")
        outFilePath = os.path.join(testDir, str(i) + ".out")
        inFile = open(inFilePath)
        outFile = open(outFilePath)

        out, elapsedTime, memoryUsage = runProcess(executablePath, inFile)
        paddedI = str(i).ljust(3, " ")
        genericFailMessage = f"  Test case #{paddedI} {ANSI_RED}failed{ANSI_RESET}"

        if elapsedTime > TIME_LIMIT:
            print(
                f"{genericFailMessage}. Program ran in {elapsedTime:.3f} seconds, while time limit was set to {TIME_LIMIT} seconds"
            )
            continue
        if memoryUsage > MEMORY_LIMIT:
            print(
                f"{genericFailMessage}. Program used {memoryUsage:.3f} MB of memory, while memory limit was set to {MEMORY_LIMIT} MB"
            )
            continue

        outLines = sum(1 for _ in open(outFilePath))
        if len(out) != outLines:
            print(
                f"{genericFailMessage}. Expected {outLines} lines of output, but got {len(out)} instead"
            )
        else:
            failed = False
            for j in range(outLines):
                expectedLine = outFile.readline().strip()
                if out[j] != expectedLine:
                    failed = True
                    outDiff = [ANSI_GREEN]
                    prevWasWrong = False
                    for k, c in enumerate(out[j]):
                        if k >= len(expectedLine):
                            break
                        if c != expectedLine[k] and not prevWasWrong:
                            outDiff += ANSI_RED
                            prevWasWrong = True
                        elif c == expectedLine[k] and prevWasWrong:
                            outDiff += ANSI_GREEN
                            prevWasWrong = False
                        outDiff += c
                    outDiff += ANSI_RESET
                    outDiff = "".join(outDiff)
                    print(f"{genericFailMessage}")
                    print(f"    {ANSI_CYAN}Expected{ANSI_RESET}: {expectedLine}")
                    print(f"    {ANSI_YELLOW}Found{ANSI_RESET}: {outDiff}")
                    break

            if not failed:
                print(
                    f"  Test case #{paddedI} {ANSI_GREEN}passed{ANSI_RESET} in {elapsedTime:.3f} seconds with {memoryUsage:.3f} MB of memory"
                )

        inFile.close()
        outFile.close()


if __name__ == "__main__":
    main()
