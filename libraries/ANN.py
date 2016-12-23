import numpy as np


class ANN:
    ''' This is an artificial neural network'''

    def __init__(self, numLayers, Input, target, hiddenNeuronList=[], eta=0.1):
        self.numLayers = numLayers
        self.numHiddenLayers = numLayers - 2
        self.eta = eta
        self.__Input__ = np.matrix(Input).T
        self.number_of_features = self.__Input__.shape[0]
        self.number_of_training_points = self.__Input__.shape[1]

        self.__Input__ =  np.vstack([self.__Input__,[1]*self.number_of_training_points])
        self.set_target(target)
        if not len(hiddenNeuronList):
            # Should be changed later to something more general
            self.hiddenNeuronList = [self.number_of_features]*self.numHiddenLayers
        else:
            self.hiddenNeuronList = hiddenNeuronList

        self.construct_network()
        print "Network constructed with {} layers, learning rate is {}".format(self.numLayers, self.eta)
        self.connect_layers()
        print "Layers connected"

    def set_target(self, target):
        ''' Setting target to the ANN'''
        try:
            np.shape(self.__Input__)[0] == len(target)
            self.target = np.array(target)
        except:
            return "Lengths of input and target don't match"

    def construct_network(self):
        # Input layer Stuff
        self.input_layer = input_layer(self.number_of_features)
        
        # Create Hidden Layers
        self.hidden_layers = [hidden_layer(self.hiddenNeuronList[i], self.number_of_training_points, self.eta ) for i in range(self.numHiddenLayers)]

        # Create output layer
        self.output_layer = output_layer(1, self.number_of_training_points, self.eta )

        self.layers = [self.input_layer] + self.hidden_layers + [self.output_layer]

    def connect_layers(self):
        '''Connect layers'''
        # Input layer
        self.hidden_layers[0].connect_layer(self.input_layer)
        # Hidden layers
        for n in range(self.numHiddenLayers-1):
            self.hidden_layers[n+1].connect_layer(self.hidden_layers[n])
        # Output layer
        self.output_layer.connect_layer(self.hidden_layers[-1])

    def __error_function__(self, t, o):
        '''This is the error function'''

        return (1./2)*(np.sum(np.square(t-o)))

    def backpropagate(self, target):
        self.output_layer.backpropagate(target)
        for layer in self.hidden_layers[::-1]:
            layer.backpropagate()

    def update_weights(self):
        for layer in self.layers[1:]:
            layer.update()

    def compute_forward(self):
        self.input_layer.compute_layer(self.__Input__)
        for layer in self.hidden_layers:
            layer.compute_layer()
        self.output_layer.compute_layer()

    def iterate(self, iterations):
        error = []
        for i in range(iterations):
            self.compute_forward()
            self.backpropagate(self.target)
            self.update_weights()
            error.append(self.__error_function__( self.target, self.output_layer.output[0]))
        return error


class neuron_layer:
    ''' This is a neural network layer'''

    def __init__(self, N, numDataPoints, eta):
        if isinstance(self, hidden_layer):
            self.N = N+1 # Adding bias neurons to the hidden layers
        else:
            self.N = N
        self.neurons = [neuron(self, index) for index in range(self.N)]
        self.eta = eta
        self.output = np.zeros((self.N,numDataPoints))
        self.delta = np.zeros(self.N)

    def connect_layer(self, prev_layer):
        self.prev_layer = prev_layer
        self.index = self.prev_layer.index + 1
        prev_layer.set_next_layer(self)
        numEdges = prev_layer.N * self.N
        for n in self.neurons:
            n.initialize_weights(prev_layer.N)

    def compute_layer(self):
        for i,n in enumerate(self.neurons):
            self.output[i] = n.compute()
            n.set_w_out()
        return self.output

    def update(self):
        for i, neuron in enumerate(self.neurons):
            neuron.change_weight(self.eta)

class input_layer(neuron_layer):
    ''' This is the input layer'''

    def __init__(self, N):
        self.N = N + 1 
        self.index = 0
    
    def compute_layer(self,x):
        self.output = x
        return self.output 
    
    def set_next_layer(self, next_layer):
        self.next_layer = next_layer

class hidden_layer(neuron_layer):

    def set_next_layer(self, next_layer):
        self.next_layer = next_layer

    def backpropagate(self):
        next_delta = self.next_layer.delta
        for i, neuron in enumerate(self.neurons):
            self.delta[i] = neuron.set_delta( np.sum (neuron.output * (1. - neuron.output) * np.dot(neuron.w_out, next_delta)))

class output_layer(neuron_layer):

    def backpropagate(self, target):
        for i, neuron in enumerate(self.neurons):
            self.delta[i]  = neuron.set_delta( np.sum((target - neuron.output) * neuron.output * (1 - neuron.output)))

class neuron:
    '''Units inside a layer'''

    def __init__(self, layer, index):
        self.layer = layer
        self.index = index

    def set_w_out(self):
        if isinstance(self.layer, output_layer): 
            self.w_out = None
        elif isinstance(self.layer, hidden_layer):
            w_out = [n.w[self.index] for n in self.layer.next_layer.neurons]
            self.w_out = np.array(w_out)         

    def initialize_weights(self, numInputs):
        self.w = np.random.uniform(-1, 1, numInputs)
        # self.w = np.zeros(numInputs) # Just for kicks

    def sigmoid(self, x):
        ''' This is our activation function. '''
        return 1/(1+np.exp(-x))

    def compute(self):
        if not (isinstance(self.layer, hidden_layer) and self.index == 0):
            self.output = self.sigmoid(np.ravel(np.dot( np.transpose(self.w), self.layer.prev_layer.output)))
        else:
            self.output = np.ones(self.layer.prev_layer.output.shape[1]) #Bias units outputing ones all the time.
        return self.output

    def set_delta(self, delta):
        self.delta = delta
        return self.delta

    def change_weight(self, eta):
        self.w += eta * np.sum(self.delta * self.layer.prev_layer.output)