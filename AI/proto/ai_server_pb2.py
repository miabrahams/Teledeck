# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ai_server.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0f\x61i_server.proto\x12\x0cimage_scorer\"$\n\x0fImageUrlRequest\x12\x11\n\timage_url\x18\x01 \x01(\t\"\x1c\n\x0bScoreResult\x12\r\n\x05score\x18\x01 \x01(\x02\x32W\n\x0bImageScorer\x12H\n\nPredictUrl\x12\x1d.image_scorer.ImageUrlRequest\x1a\x19.image_scorer.ScoreResult\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ai_server_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_IMAGEURLREQUEST']._serialized_start=33
  _globals['_IMAGEURLREQUEST']._serialized_end=69
  _globals['_SCORERESULT']._serialized_start=71
  _globals['_SCORERESULT']._serialized_end=99
  _globals['_IMAGESCORER']._serialized_start=101
  _globals['_IMAGESCORER']._serialized_end=188
# @@protoc_insertion_point(module_scope)