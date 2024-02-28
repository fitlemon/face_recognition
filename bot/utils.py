from deepface import DeepFace
import numpy as np
from cv2 import imread
from typing import Union, List
import psycopg2 as pg
from environs import Env
import logging


env = Env()
env.read_env('../.env', recurse=False)
COSINE_THRESHOLD = 0.68


async def img2nparray(img_path: Union[str, np.ndarray]) -> np.ndarray:
    img_obj_bgr = imread(img_path)
    return img_obj_bgr


async def img2embedding(img: Union[str, np.ndarray]):
    try:
        representation = DeepFace.represent(img, model_name='ArcFace')
        embedding = representation[0]['embedding']
        print("embedding", embedding)
        print(embedding[0])
        return embedding
    except ValueError as er:
        return None


async def find_cosine_distance(
    source_representation: Union[np.ndarray, list], test_representation: Union[np.ndarray, list]
) -> np.float64:
    if isinstance(source_representation, list):
        source_representation = np.array(source_representation)

    if isinstance(test_representation, list):
        test_representation = np.array(test_representation)

    a = np.matmul(np.transpose(source_representation), test_representation)
    b = np.sum(np.multiply(source_representation, source_representation))
    c = np.sum(np.multiply(test_representation, test_representation))
    return 1 - (a / (np.sqrt(b) * np.sqrt(c)))


### Потом сделать connection pool
async def find_similar_face(test_embedding, test_img):
    try:
        conn=pg.connect(
            dbname='maska',
            user='postgres',
                password= env.str('PSQL_PASSWORD'),
                host='localhost',
                port='5432' )
        cursor = conn.cursor()       
        # Проверяем наличие пользователя
        cursor.execute(f"SELECT * FROM faces ORDER BY embeddings <=> %s::vector LIMIT 1", (test_embedding,))
        closest_face = cursor.fetchall()
        closest_face = closest_face[0]
        conn.close()
        logging.info(f"Выгружен эмбеддинг из БД. Соединение с PostgreSQL закрыто")
        source_embedding = closest_face[3]
        # cosine_distance = await find_cosine_distance(source_embedding, test_embedding)
        verification = DeepFace.verify(test_img, f"photos/database/{closest_face[2]}")
        similar_face = {}
        similar_face['embedding'] = source_embedding
        similar_face['img_name'] = closest_face[2]
        similar_face['name'] = closest_face[1]
        similar_face['verified'] = verification['verified']
        return similar_face       
    except pg.Error as error:
        logging.info("Ошибка при работе с PostgreSQL", error)
        return {}
