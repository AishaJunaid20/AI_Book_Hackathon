---
sidebar_label: 'ROS 2 Communication Primitives'
sidebar_position: 2
---

# ROS 2 Communication Primitives

## Understanding Nodes, Topics, Services, and Basic Data Flow

In ROS 2, communication between different software components happens through several key building blocks. Understanding these building blocks is essential to grasping how robots built with ROS 2 function as coordinated systems.

### Nodes
Nodes are the basic building blocks of any ROS 2 system. Each node represents a single process that performs a specific function. Think of nodes as individual workers in a factory, each with their own specialized job. Nodes can send data, receive data, provide services, or request services from other nodes.

### Topics
Topics enable a send-receive communication model. When a node sends data to a topic, all nodes receiving data from that topic get the information. This creates a one-to-many communication pattern. Topics are perfect for continuous data streams like sensor readings, robot location information, or camera images.

### Services
Services implement a request-response communication pattern. A requesting node sends a question to a service, and the service node processes the question and returns an answer. This is ideal for operations that need immediate results, like asking for a specific action or checking the state of a system.

### Actions
Actions are used for tasks that take time to complete. They combine features of both topics and services, allowing for updates during execution, goal management, and final result reporting.

## Message Passing Concepts: Send-Receive (Publish-Subscribe)

The send-receive model is the foundation of ROS 2 communication. It works on the principle of loose connection:

- Nodes that send information don't need to know who will receive it
- Nodes that receive information don't need to know who sent it
- The ROS 2 system handles moving messages between sending and receiving nodes

This model provides several benefits:

- **Scalability**: Multiple receiving nodes can get the same data stream
- **Flexibility**: Nodes can be added or removed without affecting others
- **Robustness**: If one node fails, it doesn't necessarily affect others

## Real-Time Considerations and Modularity

ROS 2 was designed with time-critical systems in mind, offering several features to support applications where timing matters:

### Quality of Service (QoS) Settings
QoS settings allow adjusting communication behavior based on application needs:
- Reliability: Whether messages must be delivered (reliable) or can be skipped (best effort)
- Durability: Whether messages are saved for late-joining receivers (transient local) or only sent to active receivers (volatile)
- History: How many messages to keep in the queue

### Real-Time Support
ROS 2 includes support for real-time operating systems and predictable execution, making it suitable for applications where timing is critical.

### Modularity Benefits
The modular design of ROS 2 provides:
- Independent development of components
- Reusability across different robot platforms
- Easier debugging and testing
- Scalability from simple to complex systems

## Conceptual Examples

Here are some conceptual examples of how these building blocks work together in a robotic system:

### Example 1: Mobile Robot Navigation
- A sensor node sends laser scan data to a `/scan` topic
- A localization node receives `/scan` data and sends robot position to `/amcl_pose`
- A path planning node receives position data and sends navigation goals
- A motion control node receives navigation commands and controls the robot's motors

### Example 2: Service-Based Query
- A user interface requests robot status through a `/get_robot_status` service
- The robot status service processes the request and returns current battery level, operational state, and error conditions

These examples show how ROS 2's communication building blocks enable complex robot behaviors through the coordinated interaction of many specialized components.

## Next Steps

Now that we've explored the communication primitives that form the nervous system of ROS 2, the next chapter will examine how robots are represented in ROS 2 using URDF ([Humanoid Representation with URDF](./urdf-humanoid-representation)).