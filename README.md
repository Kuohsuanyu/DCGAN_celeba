# DCGAN_celeba
嘗試訓練人像生成器
模型架構

生成器
使用了一系列的反卷積層（Conv2DTranspose）來從隨機噪聲向量生成圖像。模型架構包含全連接層、批正則化層（BatchNormalization）、LeakyReLU 激活層和多個反卷積層。
使用了 100 維的隨機噪聲向量作為輸入，經過逐層放大和特徵提取，最終生成 28×28 的灰度圖像。

判別器（Discriminator）：
二分類模型，包含多個卷積層、LeakyReLU 激活層、Dropout 層以及最終的全連接層。其目的是區分真實圖像和生成圖像。使用L2正則化來控制模型的過擬合，並使用標籤平滑將真實樣本標籤設置為0.9。

損失函數和優化器
使用二元交叉熵損失函數（Binary Crossentropy）來計算生成器和判別器的損失。
優化器選擇了 Adam，學習率（1e-4）

訓練結果
因為圖像解析度設定為 28×28，是低解析度設定，生成圖像中能夠表現的細節有限。限制生成圖像的清晰度，無法顯示出更複雜的人臉特徵。

本次使用colab免費資源進行訓練
在經過大約 200 到 300 個 epoch 的訓練後，生成圖像的清晰度和細節達到了模型架構的能力上限。

![image](https://github.com/user-attachments/assets/a3f0bcf7-d51a-4c26-86fa-8c8b2f7493c2)

![image](https://github.com/user-attachments/assets/0f17ab8f-8684-4d54-beae-104e8bc7fb5a)

![image](https://github.com/user-attachments/assets/38631bc7-44d1-425d-83ed-cd46c1221545)

後續可以嘗試使用64*64解析度的圖片進行訓練
