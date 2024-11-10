# -*- coding: utf-8 -*-
"""DCGAN_train2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1P_GXGSYKenOCMpBJ-pMGNznOm40TrY1s
"""

# Mount Google Drive to save checkpoints and results
from google.colab import drive
drive.mount('/content/drive')

# Install necessary libraries (optional if already installed in Colab)
!pip install tensorflow
!pip install matplotlib
!pip install Pillow

import os
os.makedirs('/root/.kaggle', exist_ok=True)
!mv /content/kaggle.json /root/.kaggle/
os.chmod('/root/.kaggle/kaggle.json', 600)

!kaggle datasets download -d jessicali9530/celeba-dataset -p /content/dcgan_data --unzip

import os

image_folder = '/content/dcgan_data/img_align_celeba/img_align_celeba'
num_images = len([name for name in os.listdir(image_folder) if name.endswith('.jpg')])
print(f"Number of images in dataset: {num_images}")

import tensorflow as tf
from tensorflow.keras.layers import Dense, Reshape, Flatten, LeakyReLU, BatchNormalization, Input
from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dropout
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.regularizers import l2
import numpy as np
import matplotlib.pyplot as plt
import os
from PIL import Image
from google.colab import files

# 設定資料夾路徑
image_folder = '/content/dcgan_data/img_align_celeba/img_align_celeba'

# 設定參數
BUFFER_SIZE = 60000
BATCH_SIZE = 128
EPOCHS = 300
NOISE_DIM = 100
NUM_EXAMPLES_TO_GENERATE = 16

# 訓練時使用固定的種子，以便於比較生成結果
seed = tf.random.normal([NUM_EXAMPLES_TO_GENERATE, NOISE_DIM])

# Google Drive 路徑，用於保存模型和結果
save_dir = '/content/drive/MyDrive/dcgan_training'
os.makedirs(save_dir, exist_ok=True)

# 加載 CelebA 數據集並進行預處理
def load_celebA_images(data_dir, image_size=(28, 28)):
    images = []
    for filename in os.listdir(data_dir):
        if filename.endswith(".jpg"):
            img_path = os.path.join(data_dir, filename)
            img = Image.open(img_path).convert("L")
            img = img.resize(image_size)
            img = (np.array(img) - 127.5) / 127.5
            images.append(img)
    images = np.array(images)
    images = np.expand_dims(images, axis=-1)
    return images

# 加載數據
train_images = load_celebA_images(image_folder)
train_dataset = tf.data.Dataset.from_tensor_slices(train_images).shuffle(BUFFER_SIZE).batch(BATCH_SIZE)

# 上傳生成器和判別器模型檔案
def upload_and_load_models():
    uploaded = files.upload()  # 上傳模型文件

    generator_path = None
    discriminator_path = None

    for filename in uploaded.keys():
        if "generator" in filename:
            generator_path = filename
        elif "discriminator" in filename:
            discriminator_path = filename

    if generator_path and discriminator_path:
        print(f"Loading generator model from {generator_path}")
        generator = load_model(generator_path)
        print(f"Loading discriminator model from {discriminator_path}")
        discriminator = load_model(discriminator_path)
        print("成功載入生成器和判別器模型！")
    else:
        print("未找到上傳的生成器或判別器模型，初始化新的模型。")
        generator = build_generator()
        discriminator = build_discriminator()

    return generator, discriminator

# 定義生成器和判別器結構
def build_generator():
    model = Sequential([
        Input(shape=(NOISE_DIM,)),
        Dense(7 * 7 * 256, use_bias=False, kernel_regularizer=l2(1e-4)),
        BatchNormalization(),
        LeakyReLU(),
        Reshape((7, 7, 256)),

        Conv2DTranspose(128, (5, 5), strides=(1, 1), padding='same', use_bias=False, kernel_regularizer=l2(1e-4)),
        BatchNormalization(),
        LeakyReLU(),

        Conv2DTranspose(64, (5, 5), strides=(2, 2), padding='same', use_bias=False, kernel_regularizer=l2(1e-4)),
        BatchNormalization(),
        LeakyReLU(),

        Conv2DTranspose(1, (5, 5), strides=(2, 2), padding='same', use_bias=False, activation='tanh')
    ])
    return model

def build_discriminator():
    model = Sequential([
        Input(shape=(28, 28, 1)),
        Conv2D(64, (5, 5), strides=(2, 2), padding='same', kernel_regularizer=l2(1e-4)),
        LeakyReLU(),
        Dropout(0.3),

        Conv2D(128, (5, 5), strides=(2, 2), padding='same', kernel_regularizer=l2(1e-4)),
        LeakyReLU(),
        Dropout(0.3),

        Flatten(),
        Dense(1)
    ])
    return model

# 初始化生成器和判別器
generator, discriminator = upload_and_load_models()

# 定義損失和優化器
cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits=True)

def discriminator_loss(real_output, fake_output):
    real_loss = cross_entropy(tf.ones_like(real_output) * 0.9, real_output)
    fake_loss = cross_entropy(tf.zeros_like(fake_output), fake_output)
    return real_loss + fake_loss

def generator_loss(fake_output):
    return cross_entropy(tf.ones_like(fake_output), fake_output)

# 調整學習率
generator_optimizer = tf.keras.optimizers.Adam(1e-4)
discriminator_optimizer = tf.keras.optimizers.Adam(1e-4)

# 訓練步驟和損失曲線
gen_losses = []
disc_losses = []

@tf.function
def train_step(images):
    noise = tf.random.normal([BATCH_SIZE, NOISE_DIM])

    with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
        generated_images = generator(noise, training=True)
        real_output = discriminator(images, training=True)
        fake_output = discriminator(generated_images, training=True)
        gen_loss = generator_loss(fake_output)
        disc_loss = discriminator_loss(real_output, fake_output)

    gradients_of_generator = gen_tape.gradient(gen_loss, generator.trainable_variables)
    gradients_of_discriminator = disc_tape.gradient(disc_loss, discriminator.trainable_variables)
    generator_optimizer.apply_gradients(zip(gradients_of_generator, generator.trainable_variables))
    discriminator_optimizer.apply_gradients(zip(gradients_of_discriminator, discriminator.trainable_variables))

    return gen_loss, disc_loss

# 保存模型和損失曲線
def save_checkpoint_and_plot(epoch):
    generator.save(f"{save_dir}/generator_epoch_{epoch}.keras")
    discriminator.save(f"{save_dir}/discriminator_epoch_{epoch}.keras")

    plt.figure()
    plt.plot(gen_losses, label="Generator Loss")
    plt.plot(disc_losses, label="Discriminator Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.savefig(f"{save_dir}/loss_curve_epoch_{epoch}.png")
    plt.close()

def train(dataset, epochs):
    for epoch in range(epochs):
        gen_loss, disc_loss = 0.0, 0.0

        for image_batch in dataset:
            gen_loss, disc_loss = train_step(image_batch)

        gen_losses.append(gen_loss)
        disc_losses.append(disc_loss)

        if (epoch + 1) % 10 == 0:
            print(f'Epoch {epoch + 1}, Generator Loss: {gen_loss:.4f}, Discriminator Loss: {disc_loss:.4f}')
            generate_and_save_images(generator, epoch + 1, seed)
            save_checkpoint_and_plot(epoch + 1)

def generate_and_save_images(model, epoch, test_input):
    predictions = model(test_input, training=False)
    fig = plt.figure(figsize=(4, 4))
    for i in range(predictions.shape[0]):
        plt.subplot(4, 4, i + 1)
        plt.imshow(predictions[i, :, :, 0] * 127.5 + 127.5, cmap='gray')
        plt.axis('off')
    plt.savefig(f"{save_dir}/image_at_epoch_{epoch:04d}.png")
    plt.show()

# 開始訓練
train(train_dataset, EPOCHS)