from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

import logging
from environs import Env
import texts
import utils

router = Router()

env = Env()
env.read_env('../.env', recurse=False)


# Handler for start command
@router.message(Command('start'))
async def start_handler(msg: Message, state: FSMContext):
    '''
    Bot actions for start command
    '''
    await msg.answer(texts.hi_text)
    
    
@router.message(F.content_type == 'photo')
async def photo_hanlder(msg : Message, state: FSMContext, bot: Bot):
    if msg.photo:
        file_name = f"photos/download/{msg.photo[-1].file_id}.jpg"
        await bot.download(msg.photo[-1], destination=file_name)
        face_embedding = await utils.img2embedding(file_name)
        if face_embedding:
            similar_face = await utils.find_similar_face(face_embedding, file_name)
            if similar_face:
                photo = FSInputFile(f"photos/database/{similar_face['img_name']}")
                await msg.answer(f"Most similar person is: {similar_face['name']}")
                await bot.send_photo(chat_id=msg.chat.id, photo=photo)
            else:
                await msg.answer('Not OK(')
        else:
            await msg.answer('Face could not be detected in photo')