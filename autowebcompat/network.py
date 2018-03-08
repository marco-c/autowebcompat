import keras
from keras import backend as K
from keras.layers import Conv2D, Dense, Dropout, Flatten, Input, Lambda, MaxPooling2D, Concatenate, ActivityRegularization
from keras.models import Model
from keras.optimizers import RMSprop, Adam, Nadam, SGD


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
    MaxPooling2D(pool_size=(2, 2), strides=(2, 2))(x)

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

def create_simnet_network(input_shape):
    L2_REGULARIZATION = 0.001

    input = Input(shape=input_shape)

    # CNN 1
    vgg16 = keras.applications.VGG16(include_top=False, weights='imagenet', input_shape=input_shape)
    for layer in vgg16.layers[:17]:
        layer.trainable = False
    cnn_1 = vgg16(input)

    # CNN 2
    # Downsample by 4:1
    cnn_2 = MaxPooling2D(pool_size=(4,4))(input)
    cnn_2 = Conv2D(128, (3, 3), padding='same', activation='relu')(cnn_2)
    cnn_2 = Conv2D(128, (3, 3), padding='same', activation='relu')(cnn_2)
    cnn_2 = Conv2D(256, (3, 3), padding='same', activation='relu')(cnn_2)
    cnn_2 = Dropout(0.5)(cnn_2)
    cnn_2 = Flatten()(cnn_2)
    cnn_2 = Dense(1024, activation='relu')(cnn_2)

    # CNN 3
    # Downsample by 8:1
    cnn_3 = MaxPooling2D(pool_size=(8,8))(input)
    cnn_3 = Conv2D(128, (3, 3), padding='same', activation='relu')(cnn_3)
    cnn_3 = Conv2D(128, (3, 3), padding='same', activation='relu')(cnn_3)
    cnn_3 = Dropout(0.5)(cnn_3)
    cnn_3 = Flatten()(cnn_3)
    cnn_3 = Dense(512, activation='relu')(cnn_3)

    concat_2_3 = Concatenate()([cnn_2, cnn_3])
    concat_2_3 = Dense(1024, activation='relu')(concat_2_3)
    l2_reg = ActivityRegularization(l2=L2_REGULARIZATION)(concat_2_3)

    concat_1_l2 = Concatenate()([cnn_1, l2_reg])
    output = Dense(4096, activation='relu')(concat_1_l2)

    return Model(input, output)

def create(input_shape, network='vgglike', weights=None):
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
