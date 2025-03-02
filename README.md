# Newtek LightWave Plugins

### assemble-layers.py
Use for final part assembly from separate operations that stored on dedicated layers. Part can be assembled and re-assembled reliably every time change is made to any individual operation. As Modeler operations are destructive, iterative changes are very difficult to implement without time consuming rebuild of the final part assembly, especially if it consists of many steps. With this plugin part can be re-assembled in under a second with exact precision and repitability.

Part assembly is achieved by running the plugin that uses layers' names as a build instruction. Up to 100 parts can be assembled in one go, but can be easily changed in the plugin code.

The layer naming convention is:
* Layer name can contain any text/description
* Assembly instruction must be in curly brackets (`{}`)
* Assembly instruction contains step identifier
* Steps execute in reverse from depth to root, e.g. `{1.1.1}`, `{1.1.2}`, `{1.1.3}`, ... then `{1.1}`, then `{1}`
* Operations are additive (copy-paste) by default
* Substractive operation is done by adding `-` after operation ID, e.g. `{1.1.2-}`

Here's a screenshot of the potential setup:

![image](https://github.com/user-attachments/assets/e4886b81-af52-4eef-90ba-85bb6a32ac73)

Demo LightWave LWO file is also uploaded together with plugin to demonstrate the layer steps logic. Running the plugin with demo file should create 2 separate parts on 2 separate layers, that can be easily exported to STL file for slicing and 3D printing.

Open the model and run plugin:

![image](https://github.com/user-attachments/assets/0ffcd463-428f-4df7-9901-9bd1dfee362e)

Part 1 created:

![image](https://github.com/user-attachments/assets/f5efed46-7626-4e6a-b514-cacf824d0893)

Part 2 created:

![image](https://github.com/user-attachments/assets/16cd30cd-0703-450e-be28-1f35e4b7bc04)
