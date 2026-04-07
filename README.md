# **CMPT 371 A3 Socket Programming `Walkie-Talkie`**

**Course:** CMPT 371 \- Data Communications & Networking  
**Instructor:** Mirza Zaeem Baig  
**Semester:** Spring 2026  
<span style="color: purple;">***RUBRIC NOTE: As per submission guidelines, only one group member will submit the link to this repository on Canvas.***

## **Group Members**

| Name | Student ID | Email |
| :--- | :--- | :--- |
| William Ho | 301567599 | wnh1@sfu.ca |
| Steven Shijia Zhang | 301584110 | ssz6@sfu.ca |

## **1\. Project Overview & Description**

Our project is a simple "Walkie Talkie" application that is builting using mainly Python's Socket API (TCP) and an external library called sounddevice. It allows for multiple clients to connect to a central server and communication between the different clients by holding a push-to-talk button on the GUI.

## **2\. System Limitations & Edge Cases**

As required by the project specifications, we have identified and handled (or defined) the following limitations and potential issues within our application scope:

* **Handling Multiple Clients Concurrently:** 
  * <span style="color: green;">*Solution:*</span> We used Python's Thread library to handle multiple clients connecting at the same time by making a new thread for each client connecting to the server letting the server talk to clients simultaneously without any one of them blocking each other. This allowed for the core functionality of our project. 
  * <span style="color: red;">*Limitation:*</span> Thread creation is limited by the server's system resources. In a severe situation with a large amount of conurrent clients connected to the server, the server may experience lag causing major delay or loss of packets when broadcasting the packets to all clients.
* **Reconnection Logic:** 
  * <span style="color: red;">*Limitation:*</span> In the case of a client crashing while connected to a server, we do not have any logic that handles reconnection meaning that every client has to manually connect or disconnect. 
* **Security:** 
  * <span style="color: red;">*Limitation:*</span> Our application is fairly basic and does not implement sort of security measures and that means anyone who can reach the server can connect to the walkie talkie. That means someone with malicious intentions can connect to the server effectively start a DDoS attack by sending a massive payload slowing down the server.
* **Getting Audio Input**
  * <span style="color: green;">*Solution:*</span> We did some research and came across 2 external libaries that could be used with capturing audio input which are pyaudio and sounddevice. We chose sounddevice as we found it to be more easy to use.
  * <span style="color: red;">*Limitation:*</span> Something that we did not consider however and realized after building our application is that we did not implement letting only one client speak at a time. For our current implentation multiple clients can talk over eachother, however if we had more time we would've probably solved this issue using mutex locks.
* **Functionality using a real local IP address**
  * <span style="color: red;">*Limitation:*</span> We couldn't find a way to connect multiple devices to a server's local IP address without revealing the server's real local IP address since the client's needed to explicitly type in the server's ip address to connect.
  * <span style="color: green;">*Solution:*</span> For the sake of simplicity, we decided to hardcode ip address to tbe the localhost. However in the future if we did implement a way for it to work on a local network, we would probably do something similar to [this](https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib)

## **3\. Video Demo**

<span style="color: purple;">***You can find a link to our demo below.***</span>  
Our 2-minute video demonstration covering...:  
[**▶️ Watch Project Demo on YouTube**]()

## **4\. Prerequisites (Fresh Environment)**

To run this project, you need:

* **Python 3.10** or higher.  
* We use one external library called "sounddevice". Please make sure to pip install sounddevice
* (Optional) VS Code or Terminal.

<span style="color: purple;">***NOTE: We provided a requirements.txt file that shows all libraries needed for the environment to run.***</span>

## **4\. Step-by-Step Run Guide**

### **Step 1: Start the Server**

Open a terminal and navigate to the project folder. The server binds to 127.0.0.1 on port 5050\.  
```bash
python ./src/server.py  
# Console output: "[STARTING] Walkie Talkie server on 127.0.0.1:5050"
```

### **Step 2: Connect the First Client**

Open a **new** terminal window (while keeping the server running). Make sure you are on the project folder and run the client script to start the first client.  
```bash
python ./src/client.py  
# A simple GUI should appear on your screen"
```

### **Step 3: Connect to server**

Enter the username of your choice and click the "Connect" button below to connect ot the server.
```bash  
# GUI output: "Connected to server."
# GUI output: "[INFO] Connected as (USERNAME). Hold SPACE to talk."

```

### **Step 4: Connect a Second Client**

Open a third **new** terminal window (while still keeping the other terminals running). Make sure you are on the project folder and repeat step 3.
```bash
# On the first GUI, you should see another message in the log box
# GUI1 output: "[INFO] (USERNAME2) joined."

# GUI2 output: "Connected to server."
# GUI2 output: "[INFO] Connected as (USERNAME2). Hold SPACE to talk."
```

### **Step 5: Start your Walkie Talkie Experience**

To begin simply hold your **SPACE BAR** or click and hold on the **Hold to Talk Button** below your connection status.
Since this is all done on your local machine, you should hear your own voice like an echo.

### **Step 6: Exiting the Walkie Talkie***

When you're done, simply click the X in the top right of the GUI to exit. A message will pop up on other client's log box letting them know you have left.
```bash 
# You will see a message in the log box when one of the client(s) leave
# GUI ouput: "[INFO] (USERNAME) left.
```

## **5\. Technical Protocol Details (JSON over TCP)**

We designed a custom application-layer protocol for data exchange using JSON over TCP:

* **Message Format:** `{"type": <string>, ... fields}` which is then terminated with a **\n** character.  
* **Handshake Phase:** \* Client sends: `{"type": "CONNECT", "username": "EXAMPLE"}`  
  * Server responds: `{"type": "INFO", "message": "Connected as EXAMPLE. Hold SPACE to talk"}`  
* **Audio Transmission Phase:**  
  * Client sends: `{"type": "AUDIO", "payload": "<base64-encoded PCM audio>"}`  
  * Server broadcasts to all other clients: `{"type": "AUDIO", "from": "EXAMPLE", "payload": "base64-encoded PCM audio"}`
* **Disconnect Phase:**
  * Client sends: `{"type": "DISCONNECT"}`
  * Sever removes the client and broadcasts: `{"type": "INFO", "message": "EXAMPLE has left."}`
* **Error Handling:**
  * Server Sends: `{"type": "ERROR", "message":, "<error description>"}`


## **6\. Academic Integrity & References**

* **Code Origin:**  
  * The core multithreaded logic and protocol were written by the us. While we wrote most of the GUI, we had ChatGPT help is refine it as we were unfamilliar with using tkinter.
* **GenAI Usage:**  
  * ChatGPT was used to assist in creating a simple GUI for our project.   
* **References:**  
  * [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)  
  * [Real Python: Intro to Python Threading](https://realpython.com/intro-to-python-threading/)
  * [External library used for audio input](https://pypi.org/project/sounddevice/)



