# Пегтымельские петроглифы

Проект НИУ Высшая школа экономики и Института археологии РАН:
Численный анализ Пегтымельских петроглифов.

Проект посвящён анализу изображений оленей с целью кластеризации по стилю. В этом репозитории собираются коды, использованные для подготовки и анализа данных.

Ссылка на текст статьи: https://docs.google.com/document/d/1_vS1hlmprwnuXpy-oE6KseHAr0MnXy83/edit

Ссылка на данные разной степени обработки: https://docs.google.com/document/d/1THrl8PfusUq4fwYRrBhKwi7_u9Um5BkAjdac-vcJFmY/edit

markup.py - разметчик ключевых точек на изображениях

image_adjustment - код для первичной обработки изображений

GAN - обучение генеративно-состязательной нейросети (реализованной на библиотеке Keras) на датасете MNIST, работа с латентным пространством признаков, доп обработка оленьих изображений для сети и обучение на оленях 

fool_contours_clean code - выделение контуров

sizes - получение расстояний по координатам точек

Куратор: Павел Лебедев

Участники:
Глотова Анастасия,
Локонцева Ксения,
Магомедов Ахмед,
Сысоева Мария
