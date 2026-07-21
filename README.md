# HackRF One WiFi Jamming & Spectrum Analysis Toolkit

This project is a Python-based software-defined radio (SDR) tool designed to scan, detect, and disrupt wireless communications on target frequency bands. Utilizing a HackRF One device and OsmoSDR flow graphs, the script systematically monitors channel activity and selectively executes targeted interference to study wireless spectrum vulnerabilities.

## 📖 Introduction & Motivation

Understanding wireless communication vulnerabilities is essential for building resilient defense strategies. Jamming mechanisms are classified by both their **transmission pattern**:

* **Constant Jamming:** Emits signals continuously across a target frequency to block channel access.
* **Transition Jamming:** Shifts across multiple frequency channels systematically.
* **Random Jamming:** Emits interference across pseudo-random frequencies or time slots.

and their **reactivity**:
* **Proactive Jamming ("Blind"):** Transmits interference continuously or blindly regardless of whether actual network traffic is present.
* **Reactive Jamming ("Smart"):** Remains idle and monitors the channel, triggering transmission **only** when active communication or traffic is detected.

> **What This Project Uses:**
> This project specifically implements **Reactive Transition Jamming**. It systematically transitions (hops) across multiple frequency channels, uses a sensing function to evaluate channel activity against a power threshold and reactively triggers jamming transmissions only when active channel usage is identified.

## 🛠️ Technologies

* **HackRF One:** The primary SDR hardware peripheral used for real-time radio frequency operations. The project specifically employes a dual-device configuration:
  * *Device 1:* Dedicated to passive data collection and channel sensing (`sense`).
  * *Device 2:* Dedicated to active jamming and disrupting the targeted channel (`jam`).
* **HackRF Spectrum Analyzer:** A companion visualization interface and analysis tool used for real-time monitoring of spectrum usage, channel activity, and the visual impact of jamming operations (hardware specs and utility details can be found via the [HackRF Spectrum Analyzer repository](https://github.com/pavsa/hackrf-spectrum-analyzer)).
* **SMA Cable:** Utilized for physically connecting and ensuring precise hardware synchronization between the devices.
* **GNU Radio:** Acts as the graphical framework used to design signal processing flow graphs by arranging functional blocks. Once the blocks are configured, GNU Radio automatically generates the underlying Python code required to execute the flow graph logic, handling both hardware interfacing and signal stream manipulation.
* **Linux OS Environment:** The central host operating system required for low-level device control, script execution and configured USB user permissions.


## ⚙️ Code Logic

The script relies on a continuous scanning loop driven by core functional components:

* **`set_freq(freq)`:** 
  Dynamically tunes the SDR hardware to the target frequency, ensuring seamless channel switching during the transition-hopping phase without restarting the entire flow graph.
* **`sense(freq, delay)`:** 
  Tunes the SDR source to the target frequency and reads incoming samples over a short sensing duration (`T_SENSING`). Passes the captured signal through a low-pass filter and a magnitude squared block, writing the raw power output data to a temporary file (`output.bin`).
* **`detect()`:** 
  Evaluates the power data from `output.bin` against a predefined power `THRESHOLD` to check for active channel utilization and decides whether disruption is necessary.
* **`jam(freq, waveform, power, delay)`:** 
  Triggered only when the sensed power exceeds the active threshold. Configures the selected jamming waveform (such as Gaussian noise or tones) and sets transmission radio frequency gains based on power parameters, automatically executing the active disruption signal on the target frequency for the specified duration (`T_JAMMING`).

> **Note:**
> GNU Radio provides the underlying code skeleton for hardware communication and core signal processing (such as stream connections, flow graphs, and block initializations). Custom logic (including the scanning loop, `set_freq`, channel sensing threshold evaluations and conditional `jam` triggers) is then built around this generated foundation to control real-time reactive behavior.

## 🚀 Setup and Configuration

To run this script successfully, ensure your environment meets the following requirements:

### Dependencies & OS
* **Operating System:** A Linux system with GNU Radio (v3.8+) and the `osmosdr` Python modules installed, along with other required Python dependencies.
* **Required System Packages:** Ensure the following packages are installed (exact names depend on your Linux distribution):
```bash
sudo apt install libusb-1.0 libfftw3-bin default-jdk
```

### Hardware & Physical Connections
* **SDR Setup:** Connect the HackRF One devices to your Linux machine using Micro-USB cables.
* **Cable Connection:** Connect an SMA cable directly between the two HackRF devices.
* **Device Identification:** Check the device serial numbers and map them to the correct roles in the code under the `args` parameter (to distinguish between sensing and jamming devices).
```python
  osmosdr_source = osmosdr.source(
      args="numchan=" + str(1) + " " + ""
  )
```
