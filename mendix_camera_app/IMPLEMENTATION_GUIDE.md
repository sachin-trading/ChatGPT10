# Mendix Native Mobile Camera Application Implementation Guide

This document provides a detailed, step-by-step guide to creating a Mendix Native Mobile application that loads an image from the camera without using any Python code.

## 1. Prerequisites
- **Mendix Studio Pro** (Version 9.x or 10.x recommended).
- **Native Mobile Resources** module (Downloadable from the Mendix Marketplace).
- **Make it Native** app on your mobile device (for testing).

## 2. Domain Model Setup
The Domain Model defines how the image data is stored.

1. Open your Mendix project.
2. Navigate to the **Domain Model** of your main module (e.g., `MyFirstModule`).
3. Create a new Entity named `CapturedImage`.
4. Double-click the entity and set **Generalization** to `System.Image` (found in the `System` module).
5. (Optional) Add an attribute `CaptureTime` (DateTime) to track when the image was taken.

## 3. UI Design (Native Mobile Page)
Create a page for the user to interact with.

1. Right-click your module and select **Add page**.
2. Select the **Native Mobile** category and choose a template (e.g., "Blank").
3. Name the page `ImageCapture_Native`.
4. Add a **Data View** widget to the page.
   - Set the Data Source to **Microflow/Nanoflow** or **Context** (depending on how you navigate to this page). If it's a standalone page, you might want a Nanoflow that returns a new `CapturedImage` object.
5. Inside the Data View, add:
   - An **Image Viewer** widget: Set the data source to the `CapturedImage` entity.
   - A **Button**: Label it "Take Photo".

## 4. Nanoflow Logic (The "Code")
Mendix uses Nanoflows for device-side logic.

1. Create a new **Nanoflow** named `ACT_TakePhoto`.
2. Add a Parameter of type `CapturedImage` (matching the object in your Data View).
3. Add an Activity from the **Native Mobile Resources** category called **Take Picture**.
   - **Picture Object**: Select your `CapturedImage` parameter.
   - **Picture Source**: Set to `Camera` (this forces the camera to open).
   - **Quality**: Original or Medium.
4. (Optional) Add a **Save Changes** activity to persist the image locally.
5. Add an **End Event**.

## 5. Connecting the Dots
1. Go back to your `ImageCapture_Native` page.
2. Select the "Take Photo" button.
3. Set the **On Click** action to **Call a Nanoflow**.
4. Select `ACT_TakePhoto`.
5. Ensure the button passes the `CapturedImage` object from the Data View to the Nanoflow.

## 6. Deployment & Testing
1. Click **Run Locally** in Mendix Studio Pro.
2. Use the **Make it Native** app to scan the QR code.
3. Tap the "Take Photo" button. The app will request camera permissions and open the camera.
4. Once the photo is taken, it will be loaded into the `CapturedImage` object and displayed in the Image Viewer.

---
*Note: This solution is entirely low-code and does not require Python or any custom JavaScript coding unless specific custom enhancements are needed.*
