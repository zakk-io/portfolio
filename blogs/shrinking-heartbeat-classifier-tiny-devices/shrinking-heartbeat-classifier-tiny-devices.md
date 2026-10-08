# How I Shrank a Heartbeat Classifier for Tiny Devices

---



**Problem:** Cloud-based ECG analysis sends sensitive heart recordings off-site to a remote server, exposing patient data outside the clinic's control. It also makes every result depend on the network: each request has to travel to the server and back, and in a clinic without a reliable internet connection there may be no result at all. Running the model on the device itself avoids both problems, but edge hardware has very little memory and computing power, so the model has to be made small enough to fit without giving up too much accuracy.

**Next:** Deploy the model on a microcontroller, the kind of small, low-power chip that could run inside a portable ECG device without needing a laptop, a phone or an internet connection.

The work comes from my AI Research & Engineering internship at the Università degli Studi di Parma in July 2026, funded by Erasmus+. During that month I built and evaluated an ECG classification system around a quantized TensorFlow Lite model, working with researchers at the university.

The model is small. It takes one heartbeat (140 samples, from the ECG5000 dataset) and puts it into one of five classes: Normal, RonTPVC, PVC, SPEB or Unclassified. It has three layers and 5,125 parameters, and the whole file is 9,104 bytes. Before the model sees anything, a separate step reads the heartbeat signal off an image of a printed ECG strip.

The code is on GitHub: [github.com/zakk-io/ECG-Classification-API](https://github.com/zakk-io/ECG-Classification-API)

---

## Part 1: Edge computing, and why we need it

### What it is

Most AI you use today runs in the cloud. Your phone or device collects the data, sends it to a big server somewhere, and waits for the answer to come back.

Edge computing flips that around. The model runs on the device that collected the data, or on something close to it, like a phone, a small computer in the clinic, or a chip inside a medical sensor. The data doesn't have to travel anywhere.

### Why it matters, especially for health

Picture a nurse in a rural clinic with a paper ECG strip and a patient waiting. Sending everything to a server creates four problems:

- It's slow. Every request has to cross the network and back. On a device, the answer can come back in milliseconds.
- It needs internet. Many clinics don't have a reliable connection. A model on the device keeps working offline.
- It moves private data around. Heart recordings are sensitive. If the model runs locally, the data never leaves the room.
- It sends a lot of data. In my tests a strip image was about 5.6 KB, the extracted heartbeat was 140 bytes, and the final answer was a single byte. Doing the work on the device means you only ever send the answer, if anything.



---

## Part 2: Quantization, and why we need it

### What it is

Neural networks normally store every number as a 32-bit decimal. That's very precise: a 32-bit number can take about 4 billion different values. But a network doesn't need that much precision to make a good decision.

Quantization stores each number in 8 bits instead. An 8-bit number can only take 256 values, so every weight gets rounded to the closest of those 256. It's a bit like describing a photo with 256 colours instead of millions. You lose fine detail, but the picture is still clearly the same.




---
## Part 3: Making my own test images

### Why I had to

The ECG5000 dataset contains heartbeats as lists of numbers, not as pictures. But my system is meant to work from images of printed ECG strips. I couldn't find a set of strip images where I also knew the exact signal and the correct class behind each one, and without that I'd have no way of checking whether my system read the image correctly.

So I made my own. I wrote a script that takes each heartbeat from the test set and draws it the way an ECG machine would print it. Because I drew every image myself, I know exactly what's in it. That let me answer three separate questions:

- How good is the model on its own, with the perfect digital signal?
- How much is lost when the signal has to be read back off an image?
- What happens when the image is messy, like a crooked phone photo or a poor scan?

### How the images are made

Each heartbeat is drawn on standard ECG paper: a pink grid with 1 mm squares, darker red lines every 5 mm, and a calibration bar in the margin, as on a real printout. To stop every image looking identical, the line thickness and ink colour vary slightly from one image to the next.

For the messy version, each image gets a "scanned" copy that is:

- tilted by up to 3 degrees
- sprinkled with random pixel noise
- made slightly darker and lower in contrast
- slightly blurred, in about a third of the images

The script also saves a list linking every image to its original heartbeat and its correct class, so every prediction can be checked automatically.

```bash
# 50 clean images, roughly 10 per class
python generate_ecg_test_images.py --n 50

# 100 images plus a messy "scanned" copy of each
python generate_ecg_test_images.py --n 100 --distort

# Full check: read each image back, classify it, and compare with the truth
python generate_ecg_test_images.py --n 50 --distort --validate
```
---

## Part 4: The results

With the concepts in place, here's how the full system performed. It takes a strip image, reads the heartbeat off it, and classifies it with the 8-bit model.

### Test setup

Everything ran on an ordinary laptop: an HP 15s with a 12th-gen Intel Core i7-1255U and 16 GB of memory. The model ran on a single CPU core, with no GPU or accelerator. That's deliberate. It's much closer to what an edge device can offer than a server with a graphics card.

### Accuracy on 1,000 strip images

The system got 927 of 1,000 images right, which is 92.7% overall. That number hides big differences between classes:

| Class | Images | Correct | Accuracy |
|---|---|---|---|
| Normal | 298 | 296 | 99.3% |
| RonTPVC | 567 | 547 | 96.5% |
| PVC | 39 | 20 | 51.3% |
| SPEB | 86 | 61 | 70.9% |
| Unclassified | 10 | 3 | 30.0% |

Normal and RonTPVC beats are handled very well. PVC and Unclassified beats are not. The confusion matrix shows where the mistakes go (rows are the true class, columns what the model predicted):

| True ↓ / Predicted → | Normal | RonTPVC | PVC | SPEB | Unclass. |
|---|---|---|---|---|---|
| Normal | 296 | 0 | 0 | 1 | 1 |
| RonTPVC | 1 | 547 | 4 | 15 | 0 |
| PVC | 2 | 11 | 20 | 4 | 2 |
| SPEB | 3 | 22 | 0 | 61 | 0 |
| Unclassified | 3 | 0 | 2 | 2 | 3 |

A few patterns stand out:

- 11 of the 39 PVC beats were called RonTPVC. The two types look alike, and RonTPVC is far more common in the data, so the model leans towards it when unsure.
- 22 of the 86 SPEB beats also ended up as RonTPVC.
- The Unclassified beats were scattered across Normal, PVC and SPEB. With only 10 examples, the model never really learned what they look like.

The underlying cause is clear in the data. The rare classes (PVC, SPEB and Unclassified) make up only a small slice of what the model was trained on, so it has seen too few of them to tell them apart reliably. More examples of those classes is the most obvious next step.

### Speed: one image at a time

A single image took 17.81 ms on average from start to finish. That's around 55 images per second on one CPU core, comfortably fast enough for a nurse waiting at a bedside.

### Speed: several requests at once

Edge devices often have just one core, so I tested what happens when requests pile up:

| Scenario | Requests | Average wait | Longest wait | Throughput |
|---|---|---|---|---|
| 1 request on its own | 1 | 17.78 ms | 17.78 ms | 54.9 per second |
| 8 requests at the exact same moment | 8 | 166.98 ms | 208.92 ms | 36.0 per second |
| 8 senders, 5 requests each, back to back | 40 | 135.21 ms | 233.10 ms | 57.3 per second |

With one core, requests can't run side by side; they wait in line. When 8 arrive at once, the first is quick (32.59 ms) and the last waits about 209 ms. The device doesn't get faster when it's busy, but it doesn't break either: throughput stays roughly the same and everything gets answered. In practice, requests rarely arrive at the exact same instant, so real use sits between the first row and the second.

### Speed: a big batch

I also sent 1,000 images in one go, three times:

| Run | Total time | Per image | Succeeded | Failed |
|---|---|---|---|---|
| 1 | 17.78 s | 17.78 ms | 1,000 | 0 |
| 2 | 19.69 s | 19.69 ms | 1,000 | 0 |
| 3 | 16.43 s | 16.43 ms | 1,000 | 0 |

The best run processed 60.8 images per second, and none of the 3,000 images failed.

### Where the time actually goes

This was the result that surprised me most. I timed the two main steps separately over 200 images:

| Step | Time per image |
|---|---|
| Reading the heartbeat off the image | 10.20 ms |
| Running the 8-bit neural network | 0.017 ms |

The neural network takes less than 0.2% of the time. Almost all of the work is in reading the signal from the picture.

That changes where effort should go. Speeding up one part of a system can only save as much time as that part was using (this is known as Amdahl's law). Even an infinitely fast model would make the whole system only about 0.17% faster. The real gains are in the image-reading step, for example by not letting the search consider big jumps between neighbouring columns, since a heartbeat line can only move so far.

I went in assuming the model was the thing to optimise. Quantization had already made it so small and fast that it stopped being the bottleneck.

---

## Part 5: Knowing when to ask a human

A device working on its own can't ask a server for a second opinion, so it needs a way to flag the cases it's unsure about. The results above show why: 92.7% overall sounds good, but PVC beats are right only about half the time.

A simple approach is to have the model skip any beat where its confidence is below some threshold and send it to a clinician instead. Using the 8-bit model's confidence scores on 1,000 test beats:

| Minimum confidence | Beats answered | Accuracy on those beats |
|---|---|---|
| none | 100% | 94.3% |
| 0.5 | 99.2% | 94.6% |
| 0.7 | 95.8% | 96.2% |
| 0.9 | 86.0% | 97.2% |

Handing the least certain 14% to a person raises accuracy on the rest from 94.3% to 97.2%. On the device, that costs a single comparison.

This is why I think of the system as an assistant, not a diagnosis tool. It can sort the clear cases quickly, and the uncertain ones, especially predicted PVC and Unclassified beats, should always be checked by a clinician.

---

## Beyond the code: my month in Parma

This project came out of a one-month AI Research & Engineering internship at the Università degli Studi di Parma in July 2026, through Erasmus+. It turned out to be one of the best experiences I've had, and the research was only part of it.

![On the way to Italy](travling%20to%20italy.jpeg)
*On my way to Italy.*

Working in a university lab abroad felt very different from studying. I got to see how researchers actually work day to day: how they think a question through before writing any code, how openly they discuss results and push back on each other's assumptions, and how carefully they check a number before they trust it. I joined the group's AI research activities and worked with researchers on model development. Watching how they worked taught me as much as the technical side did. It's also where I picked up the habit this post is built on: measure things, don't trust the headline number, and be clear about what an experiment does and doesn't show.

![Me at the lab in Parma](me%20at%20the%20lab.jpeg)
*At the lab in Parma.*

Outside the lab, I spent my time exploring Italy and its culture. Getting used to a new country and a different pace of life pushed me out of my comfort zone in a good way. Meeting people from many different backgrounds, at the university and outside it, showed me how international research really is.

![Discovering Parma](dicovering%20param%20city.jpeg)
*Discovering the city centre of Parma.*

---

## Limitations

- I didn't have the original full-precision model, so I couldn't measure how much accuracy was lost when the weights were rounded. The comparison in Part 2 only covers the 8-bit calculations.
- All the strip images were generated from known signals. Real photos would be messier.
- ECG5000 comes from a single patient, so these results don't show how the system would do in a clinic. It's a learning prototype, not a medical device.
- The class counts in the 1,000-image evaluation differ slightly from the counts in the test file, and the exact image set wasn't recorded. When I re-ran the evaluation with a fixed random seed on the test file, accuracy on clean images was 93.9%, close to the 92.7% above.
- The benchmarks ran on a laptop CPU limited to one core. They show the model is light enough for small hardware, but it hasn't yet been tested on an actual microcontroller or phone.