import onnx
import onnxruntime as ort

def load_and_inference(onnx_file, input_dict):
    onnx_model = onnx.load(onnx_file)
    onnx.checker.check_model(onnx_model)
    onnx.helper.printable_graph(onnx_model.graph)

    #To get the inputs we must ignore the initializers, otherwise it would seem like we have a lot of inputs in some cases
    input_all = [node.name for node in onnx_model.graph.input]
    input_initializer =  [node.name for node in onnx_model.graph.initializer]
    net_feed_input = list(set(input_all)  - set(input_initializer))
    # print('Inputs: ', net_feed_input)
    model_num_inputs = len(net_feed_input)

    # # Single Input ONNX File --> string
    # if model_num_inputs == 1:
    #     model_input = net_feed_input[0]
    # # Multi-Input ONNX File --> list of string
    # else:
    #     model_input = net_feed_input
    
    so = ort.SessionOptions()
    ort_session = ort.InferenceSession(onnx_file, so, providers=['CPUExecutionProvider'])

    session_input = {}
    for node_name, tensor in net_feed_input:
        session_input[node_name] = tensor

    result = ort_session.run(None, session_input)

    return_dict = {}
    outputs = onnx_model.graph.output
    # NOTE: the following supposes ordered results
    for idx, output in outputs:
        return_dict[output.name] = result[idx]

    if input_dict['keep']:
        # Forward input tensors
        for input in net_feed_input:
            return_dict[input] = input_dict[input]
    
    # Unused input must be forwarded
    for input in input_dict:
        if input not in net_feed_input:
            return_dict[input] = input_dict[input]
    
    return return_dict