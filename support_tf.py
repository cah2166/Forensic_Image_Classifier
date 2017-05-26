import tensorflow as tf, sys, support, support_sql

def classifyImage(image_path):
    # Read in image data 
    image_data = tf.gfile.FastGFile(image_path,'rb').read() # imports image

    # Loads label file. Stripes off carriage return
    label_lines = [line.rstrip() for line in tf.gfile.GFile("tf_files/retrained_labels.txt")] # acquires the labels form the restrained_labels

    # Unpersist graph from file
    with tf.gfile.FastGFile("tf_files/retrained_graph.pb", 'rb') as f: # iterates the graph 
        graph_def = tf.GraphDef()# 
        graph_def.ParseFromString(f.read())
        _=tf.import_graph_def(graph_def, name='')
    	
    with tf.Session() as sess:
        # Feed the image data as input into the graph and get first prediciton
        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
        predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})

        # Sort to show labels of first prediciton in order of confidence
        top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]

        for node_id in top_k:
            human_string = label_lines[node_id]
            score = predictions[0][node_id]
            support.msg('%s (score=%.5f)'%(human_string, score))
    return top_k, label_lines, predictions

if __name__=='__main__':
    for infile in sys.argv[1:]:
        classifyImage(infile)