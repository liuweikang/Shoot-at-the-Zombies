#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板图片加密工具
使用私钥文件内容派生密钥进行XOR加密，防止他人查看真实图片内容
加密后会输出派生密钥，需将其嵌入game_bot.py中用于解密
"""

import os
import cv2
import numpy as np
import hashlib

# 密钥目录
KEY_DIR = 'keys'
PRIVATE_KEY_FILE = 'private_key.pem'

# 模板目录和加密目录
TEMPLATE_DIR = 'templates'
ENCRYPTED_DIR = 'templates_encrypted'

def derive_key_from_private_key():
    """从私钥文件内容派生加密密钥"""
    private_key_path = os.path.join(KEY_DIR, PRIVATE_KEY_FILE)
    if not os.path.exists(private_key_path):
        print(f"私钥文件不存在: {private_key_path}")
        print("请先运行 generate_keys.py 生成密钥对")
        return None
    
    with open(private_key_path, 'rb') as f:
        private_key_pem = f.read()
    
    key = hashlib.sha256(private_key_pem).digest()
    return key

def encrypt_image(image_path, output_path, key):
    """使用派生密钥加密单个图片文件"""
    img = cv2.imread(image_path)
    if img is None:
        print(f"无法读取图片: {image_path}")
        return False
    
    img_bytes = img.tobytes()
    
    encrypted_bytes = bytearray()
    for i, b in enumerate(img_bytes):
        key_byte = key[i % len(key)]
        encrypted_bytes.append(b ^ key_byte)
    
    shape = img.shape
    with open(output_path, 'wb') as f:
        f.write(np.array(shape, dtype=np.int32).tobytes())
        f.write(encrypted_bytes)
    
    print(f"加密成功: {image_path} -> {output_path}")
    return True

def decrypt_image(encrypted_path, output_path, key):
    """使用派生密钥解密单个模板文件"""
    try:
        with open(encrypted_path, 'rb') as f:
            shape_data = f.read(12)
            shape = np.frombuffer(shape_data, dtype=np.int32)
            encrypted_bytes = f.read()
        
        decrypted_bytes = bytearray()
        for i, b in enumerate(encrypted_bytes):
            key_byte = key[i % len(key)]
            decrypted_bytes.append(b ^ key_byte)
        
        img = np.frombuffer(decrypted_bytes, dtype=np.uint8).reshape(shape)
        cv2.imwrite(output_path, img)
        print(f"解密成功: {encrypted_path} -> {output_path}")
        return True
    except Exception as e:
        print(f"解密失败: {e}")
        return False

def main():
    """加密所有模板图片"""
    key = derive_key_from_private_key()
    if not key:
        return
    
    os.makedirs(ENCRYPTED_DIR, exist_ok=True)
    
    for filename in os.listdir(TEMPLATE_DIR):
        if filename.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            image_path = os.path.join(TEMPLATE_DIR, filename)
            output_path = os.path.join(ENCRYPTED_DIR, f"{os.path.splitext(filename)[0]}.enc")
            encrypt_image(image_path, output_path, key)
    
    print(f"\n加密完成！加密后的文件保存在: {ENCRYPTED_DIR}")
    print(f"\n请将以下派生密钥嵌入 game_bot.py 的 DECRYPTION_KEY 中：")
    print(f"DECRYPTION_KEY = {key.hex()}")

def decrypt_all():
    """解密所有模板文件"""
    key = derive_key_from_private_key()
    if not key:
        return
    
    DECRYPTED_DIR = 'templates_decrypted'
    os.makedirs(DECRYPTED_DIR, exist_ok=True)
    
    for filename in os.listdir(ENCRYPTED_DIR):
        if filename.endswith('.enc'):
            encrypted_path = os.path.join(ENCRYPTED_DIR, filename)
            output_path = os.path.join(DECRYPTED_DIR, f"{os.path.splitext(filename)[0]}.png")
            decrypt_image(encrypted_path, output_path, key)
    
    print(f"\n解密完成！解密后的文件保存在: {DECRYPTED_DIR}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--decrypt":
        decrypt_all()
    else:
        main()
