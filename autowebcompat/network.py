from keras import backend as K
from keras.layers import Conv2D, Dense, Dropout, Flatten, Input, Lambda, MaxPooling2D, concatenate
from keras.models import Model
from keras.optimizers import SGD, Adam, Nadam, RMSprop

SUPPORTED_NETWORKS = ['inception', 'vgglike', 'vgg16']
SUPPORTED_OPTIMIZERS = ['sgd', 'adam', 'nadam', 'rms']


def euclidean_distance(vects):
    x, y = vects
    return K.sqrt(K.maximum(K.sum(K.square(x - y), axis=1, keepdims=True), K.epsilon()))


def eucl_dist_output_shape(shapes):
    shape1, shape2 = shapes
    return (shape1[0], 1)


def create_mlp(input_shape):
    input = Input(shape=input_shape)
    x = Flatten()(input)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.1)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.1)(x)
    x = Dense(128, activation='relu')(x)
    return Model(input, x)


def create_vgg16_network(input_shape):
    input = Input(shape=input_shape)

    # Block 1
    x = Conv2D(64, (3, 3), padding='same', activation='relu')(input)
    x = Conv2D(64, (3, 3), padding='same', activation='relu')(x)
    x = MaxPooling2D(pool_size=(2, 2), strides=(2, 2))(x)

    # Block 2
    x = Conv2D(128, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(128, (3, 3), activation='relu', padding='same',)(x)
    x = MaxPooling2D(pool_size=(2, 2), strides=(2, 2))(x)

    # Block 3
    x = Conv2D(256, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(256, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(256, (3, 3), activation='relu', padding='same')(x)
    x = MaxPooling2D(pool_size=(2, 2), strides=(2, 2))(x)

    # Block 4
    x = Conv2D(512, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(512, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(512, (3, 3), activation='relu', padding='same')(x)
    x = MaxPooling2D(pool_size=(2, 2), strides=(2, 2))(x)

    # Block 5
    x = Conv2D(512, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(512, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(512, (3, 3), activation='relu', padding='same')(x)
    x = MaxPooling2D(pool_size=(2, 2), strides=(2, 2))(x)

    x = Flatten()(x)
    x = Dense(4096, activation='relu')(x)
    x = Dropout(0.5)(x)
    x = Dense(4096, activation='relu')(x)
    # Softmax layer Not Necessary
    return Model(input, x)


def create_vgglike_network(input_shape):
    input = Input(shape=input_shape)

    # input: 192x256 images with 3 channels -> (192, 256, 3) tensors.
    # this applies 32 convolution filters of size 3x3 each.
    x = Conv2D(32, (3, 3), activation='relu')(input)
    x = Conv2D(32, (3, 3), activation='relu')(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)
    x = Dropout(0.25)(x)

    x = Conv2D(64, (3, 3), activation='relu')(x)
    x = Conv2D(64, (3, 3), activation='relu')(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)
    x = Dropout(0.25)(x)

    x = Flatten()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.5)(x)
    # x = Dense(2, activation='softmax')(x)
    x = Dense(128, activation='relu')(x)

    return Model(input, x)


def create_inception_network(input_shape):
    """
       Simple architecture with one layer of inception model

       param input_shape: shape of the input image
    """

    input = Input(shape=input_shape)

    x1 = Conv2D(64, (1, 1), activation='relu', padding='same')(input)
    x1 = Conv2D(64, (3, 3), activation='relu', padding='same')(x1)

    x2 = Conv2D(64, (1, 1), activation='relu', padding='same')(input)
    x2 = Conv2D(64, (5, 5), activation='relu', padding='same')(x2)

    x3 = MaxPooling2D((3, 3), strides=(1, 1), padding='same')(input)
    x3 = Conv2D(64, (1, 1), activation='relu', padding='same')(x3)

    x = concatenate([x1, x2, x3], axis=3)
    x = Flatten()(x)

    x = Dense(256, activation='relu')(x)
    x = Dropout(0.5)(x)
    x = Dense(128, activation='relu')(x)

    return Model(input, x)


def create(input_shape, network='vgglike', weights=None):
    assert network in SUPPORTED_NETWORKS, '%s is an invalid network' % network
    network_func = globals()['create_%s_network' % network]
    base_network = network_func(input_shape)

    input_a = Input(shape=input_shape)
    input_b = Input(shape=input_shape)

    # Loading pretrained weights corresponding to the network used
    if weights:
        base_network.load_weights(weights)

    processed_a = base_network(input_a)
    processed_b = base_network(input_b)

    '''concatenated = keras.layers.concatenate([processed_a, processed_b])
    out = Dense(1, activation='sigmoid')(concatenated)

    model = Model([input_a, input_b], out)'''

    distance = Lambda(euclidean_distance, output_shape=eucl_dist_output_shape)([processed_a, processed_b])

    return Model([input_a, input_b], distance)


def contrastive_loss(y_true, y_pred):
    '''Contrastive loss from Hadsell-et-al.'06
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    '''
    margin = 1
    return K.mean(y_true * K.square(y_pred) +
                  (1 - y_true) * K.square(K.maximum(margin - y_pred, 0)))


def accuracy(y_true, y_pred):
    '''Compute classification accuracy with a fixed threshold on distances.
    '''
    return K.mean(K.equal(y_true, K.cast(y_pred < 0.5, y_true.dtype)))


def compile(model, optimizer='sgd', loss_func=contrastive_loss):
    allOptimizers = {
        'sgd': SGD(lr=0.0003, decay=1e-6, momentum=0.9, nesterov=True),
        'adam': Adam(),
        'nadam': Nadam(),
        'rms': RMSprop()
    }
    assert optimizer in allOptimizers, '%s is an invalid optimizer' % optimizer
    opt = allOptimizers[optimizer]

    model.compile(loss=loss_func, optimizer=opt, metrics=[accuracy])
