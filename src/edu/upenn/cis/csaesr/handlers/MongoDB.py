"""A handler to access and modify a mongodb instance
"""
# Copyright (C) 2014 Taylor Turpen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from pymongo import MongoClient
from data.structures import Turker, AudioClip, Transcription, AudioSource, HitEntity
from handlers.Exceptions import MultipleResultsOnIdFind, TooManyEntries, DuplicateArtifactException
from time import time
from collections import defaultdict
import logging

class MongoHandler(object):
    default_db_loc = 'mongodb://localhost:27017'

    def __init__(self):
        client = MongoClient(self.default_db_loc)
        self.queue_revive_time = 5       
        self.db = client.transcription_db
        self.audio_sources = self.db.audio#The full audio files
        self.audio_clips = self.db.audio_clips#portions of the full audio files
        self.audio_clip_queue = self.db.audio_clip_queue#queue of the audio clips
        self.transcriptions = self.db.transcriptions
        self.reference_transcriptions = self.db.reference_transcriptions
        self.transcription_hits = self.db.transcription_hits
        self.disfluency_hits = self.db.disfluency_hits
        self.second_pass_hits = self.db.second_pass_hits
        self.turkers = self.db.turkers
        self.type_ids = self.db.type_ids
        self.assignments = self.db.assignments
        
        self.logger = logging.getLogger("transcription_engine.mongodb_handler")
        
    def insert_entity(self,entity):
        entry = entity.get_mongo_entry()
        if isinstance(entity,Turker):
            self.turkers.insert(entry)
        elif isinstance(entity,AudioClip):
            self.audio_clips.insert(entry)
        elif isinstance(entity,Transcription):
            self.transcriptions.insert(entry)
        elif isinstance(entity,AudioSource):
            self.audio_sources.insert(entry)
    
    def get_hit_by_id(self,hit_id):
        hits = self.transcripts.find({"_id" : hit_id})
        if len(hits) > 1:
            raise MultipleResultsOnIdFind(hit_id)
        hit = HitEntity(hits[0])
        return hit
    
    def get_type_ids(self):
        """All data types should have a type ID"""
        return self.type_ids.find({}) 
    
    def audio_clip_find_one(self,search,field):
        response = [w for w in self.audio_clips.find(search,{field : 1})]
        if len(response) != 1:
            raise TooManyEntries
        return response[0][field]
    
    def get_audio_clip_url(self,audio_clip_id):
        return self.audio_clip_find_one({"_id" : audio_clip_id},"audio_clip_url")
    
    def get_audio_clip_status(self,audio_clip_id):
        return self.audio_clip_find_one({"_id" : audio_clip_id},"status")
    
    def get_all_audio_clips_by_status(self,status):
        return self.audio_clips.find({"status":status})
    
    def get_all_assignments_by_status(self,status):
        return self.assignments.find({"status": status})
    
    def get_max_queue(self,max_sizes):
        max_q = []
        for q in max_sizes:
            #For each q in each q size
            if len(max_sizes[q]) >= q:
                #if the q is full
                if q > len(max_q):
                    #if the q is bigger than the q with the most clips
                    max_q = max_sizes[q][:q]
        return max_q
    
    def revive_audio_clip_queue(self):
        """If a audio clip in the queue has been processing for more than
            queue_revive_time seconds, reset its processing status"""
        non_none = self.audio_clip_queue.find({"processing": {"$ne" : None}})
        for clip in non_none:
            if  time() - clip["processing"] > self.queue_revive_time:
                self.audio_clip_queue.update({"_id":clip["_id"]}, {"$set" : {"processing" : None}})  
        self.logger.info("Finished reviving audio clip queue.")
    
    def update_audio_clip_queue(self,clip_queue):
        """Remove the audio clip entries from the clip queue"""
        for clip in clip_queue:
            self.audio_clip_queue.remove({"_id":clip["_id"]})      
        self.logger.info("Finished updating audio clip queue") 
            
    def update_audio_clip_status(self,clip_id_list,new_status):
        if type(clip_id_list) != list:
            self.logger.error("Error updating audio clip(%s)"%clip_id_list)
            raise IOError
        for clip_id in clip_id_list:
            self.audio_clips.update({"_id":clip_id},  {"$set" : {"status" : new_status}}  )   
        self.logger.info("Updated audio clip status for: %s"%clip_id_list)
        return True
    
    def create_transcription_hit_document(self,hit_id,hit_type_id,clip_queue,new_status):
        if type(clip_queue) != list:
            raise IOError
        clips = [w["audio_clip_id"] for w in clip_queue]
        self.transcription_hits.update({"_id":hit_id},
                                       {"_id":hit_id,
                                        "hit_type_id": hit_type_id,
                                        "clips" : clips,
                                        "status": new_status},
                                       upsert = True)
        self.logger.info("Updated transcription hit %s "%hit_id)
        return True
    
    def create_assignment_document(self,assignment,transcription_ids,status):
        """Create the assignment document with the transcription ids.
            AssignmentStatus is the AMT assignment status.
            status is the engine lifecycle status."""
        assignment_id = assignment.AssignmentId
        self.assignments.update({"_id":assignment_id},
                                        {"_id":assignment_id,
                                         "AcceptTime": assignment.AcceptTime,
                                         "AssignmentStatus" : assignment.AssignmentStatus,
                                         "AutoApprovalTime" : assignment.AutoApprovalTime,
                                         "hit_id" : assignment.HITId,
                                         "worker_id" : assignment.WorkerId,
                                         "transcriptions" : transcription_ids,
                                         "status": status},
                                        upsert = True)
        self.logger.info("Created Assignment document, assignment ID(%s) "%assignment_id)
        return True
    
    def create_audio_source_artifact(self,uri,disk_space,length_seconds,
                                     sample_rate,speaker_id,
                                     encoding,audio_clip_id=None,status="New"):
        """Each audio source is automatically an audio clip,
            Therefore the reference transcription can be found
            by referencing the audio clip assigned to this source.
            For turkers, speaker id will be their worker id"""        
        document = {"uri" : uri,
                    "disk_space" : disk_space,
                    "length_seconds" : length_seconds,
                    "audio_clip_id" : audio_clip_id,
                    "sample_rate" : sample_rate,
                    "speaker_id" : speaker_id,
                    "encoding" : encoding,
                    "status" : status}
        try:
            source_id = self.get_audio_source(document,field="_id")
        except TooManyEntries as e:
            self.logger.error("Duplicate artifact for document: %s"%document)            
            raise DuplicateArtifactException(document)
        if source_id: 
            return source_id
        self.audio_sources.insert(document)
        return self.get_audio_source(document,field="_id")
        
    def create_reference_transcription_artifact(self,audio_clip_id,words,level):
        """Create the reference transcription given the audio clip id
            and the transcription words themselves."""
        document = {"audio_clip_id" : audio_clip_id,
                    "transcription" : words,
                    "level" : level}
        try:
            transcription_id = self.get_reference_transcription(document,field="_id")
        except TooManyEntries as e:
            self.logger.error("Duplicate artifact for document: %s"%document)            
            raise DuplicateArtifactException(document)
        if transcription_id: 
            return transcription_id
        self.reference_transcriptions.insert(document)
        return self.get_reference_transcription(document,field="_id")
    
    def create_audio_clip_artifact(self,source_id,source_start_time,source_end_time,
                                   uri,http_url,length_seconds,
                                   disk_space,reference_transcription_id=None,
                                   status="Sourced"):
        """A -1 endtime means to the end of the clip."""
        document = {"source_id" : source_id,
                    "source_start_time" :source_start_time,
                    "source_end_time" : source_end_time,
                    "uri" : uri,
                    "http_url": http_url,
                    "length_seconds" : length_seconds,
                    "disk_space" : disk_space,
                    "reference_transcription_id" : reference_transcription_id,
                    "status" : status}
        try:
            clip_id = self.get_audio_clip(document,field="_id")
        except TooManyEntries as e:
            self.logger.error("Duplicate artifact for document: %s"%document)            
            raise DuplicateArtifactException(document)
        if clip_id: 
            return clip_id
        self.audio_clips.insert(document)
        return self.get_audio_clip(document,field="_id")
    
    def update_transcription_status(self,transcription,status):
        """Use secondary ID audio clip + assignment"""
        self.transcriptions.update({"audio_clip_id": transcription["audio_clip_id"],
                                    "assignment_id": transcription["assignment_id"]},
                                   {"assignment_id": transcription["assignment_id"],
                                    "audio_clip_id": transcription["audio_clip_id"],
                                    "transcription": transcription["transcription"],
                                    "worker_id": transcription["worker_id"],
                                    "status" : status},
                                   upsert = True)
        self.logger.info("Updated transcription w/ audio clip(%s) in assignment(%s) for worker (%s)"\
                         %(transcription["audio_clip_id"],transcription["assignment_id"],\
                           transcription["worker_id"]))
        
    def update_audio_source_audio_clip(self,source_id,clip_id):
        """For the audio source given the id, set
            the value using the document"""
        self.audio_sources.update({"_id":source_id},{"$set": {"audio_clip_id": clip_id}})
        self.audio_sources.update({"_id":source_id},{"$set": {"status" : "Clipped"}})
        
    def update_audio_clip_reference_transcription(self,clip_id,reference_transcription_id):
        self.audio_clips.update({"_id":clip_id},
                                {"$set" : {"reference_transcription_id" : reference_transcription_id}})
        
    def update_assignment_status(self,assignment,status):
        self.assignments.update({"_id":assignment["_id"]},
                                {"$set":{"status":status}})       
        
    def update_transcription_hit_status(self,hit_id,new_status):
        self.transcription_hits.update({"_id":hit_id},  {"$set" : {"status" : new_status}}  )   
        self.logger.info("Updated transcription hit(%s) status to: %s"%(hit_id,new_status))
        return True
    
    def remove_transcription_hit(self,hit_id):
        self.transcription_hits.remove({"_id":hit_id})
                
    def get_audio_clip_pairs(self,clip_queue):
        return [(self.get_audio_clip_url(w["audio_clip_id"]),w["audio_clip_id"]) for w in clip_queue]
    
    def get_audio_clips(self,field,ids):
        return [self.get_audio_clip({field: iD}) for iD in ids]
    
    def get_audio_clip(self,search,field=None,refine={}):
        responses = self.audio_clips.find(search,refine)\
                    if refine else self.audio_clips.find(search)
        prev = False
        for response in responses:
            if prev:
                raise TooManyEntries("MongoHandler.get_audio_clip")
            prev = response        
        return prev[field] if field and prev else prev
    
    def get_audio_source(self,search,field=None,refine={}):
        responses = self.audio_sources.find(search,refine)\
                    if refine else self.audio_sources.find(search)
        prev = False
        for response in responses:
            if prev:
                raise TooManyEntries("MongoHandler.get_audio_source")
            prev = response        
        return prev[field] if field and prev else prev
    
    def get_transcriptions(self,field,ids):
        return [self.get_transcription({field: iD}) for iD in ids]
    
    def get_transcription(self,search,field=None,refine={}):
        response = self.transcriptions.find(search)
        prev = False
        for response in response:
            if prev:
                raise TooManyEntries
            prev = response        
        return prev[field] if field and prev else prev
    
    def get_reference_transcription(self,search,field=None,refine={}):
        responses = self.reference_transcriptions.find(search,refine)\
                    if refine else self.reference_transcriptions.find(search)
        prev = False
        for response in responses:
            if prev:
                raise TooManyEntries
            prev = response        
        return prev[field] if field and prev else prev
    
    def queue_clip(self,audio_clip_id,priority=1,max_queue_size=3):
        self.audio_clip_queue.update({"audio_clip_id": audio_clip_id},
                             {"audio_clip_id": audio_clip_id,
                              "priority": priority,
                              "max_size": max_queue_size,
                              "processing" : None,
                              },
                             upsert = True)
        self.update_audio_clip_status([audio_clip_id], "Queued")
        self.logger.info("Queued clip: %s "%audio_clip_id)
        
    def get_audio_clip_queue(self):
        """Insert the audio clip by id into the queue.
            Get all the clips waiting in the queue and not being processed
            Find the largest queue that is full
            Update the queue and return the clips"""            
        self.revive_audio_clip_queue()
        queue = self.audio_clip_queue.find({"processing":None})
        max_sizes = defaultdict(list)
        for clip in queue:
            id = clip["_id"]
            clip_id = clip["audio_clip_id"]
            priority = clip["priority"]
            processing = clip["processing"]
            max_size = int(clip["max_size"])
            for i in range(max_size):
                max_sizes[i+1].append(clip)
        max_q = self.get_max_queue(max_sizes)        
        for clip in max_q:
            t = time()
            self.audio_clip_queue.find_and_modify(query = {"_id":clip["_id"]},
                                                 update = { "$set" : {"processing":t}}
                                                )
        return max_q
    
    def initialize_test_db(self):
        audio_clips = [{ "_id" : "12345", "audio_clip_url" : "http://www.cis.upenn.edu/~tturpen/wavs/testwav.wav", "reference" : None, "status" : "New" },
                       { "_id" : "54321", "audio_clip_url" : "http://www.cis.upenn.edu/~tturpen/wavs/testwav.wav", "reference" : None, "status" : "New" },
                       { "_id" : "98765", "audio_clip_url" : "http://www.cis.upenn.edu/~tturpen/wavs/testwav.wav", "reference" : None, "status" : "New" }]
        audio_clip_queue = [{"audio_clip_id" : "12345", "priority" : 1, "processing" : None, "max_size" : 3 },
                            {"audio_clip_id" : "54321", "priority" : 1, "processing" : None, "max_size" : 3 },
                            {"audio_clip_id" : "98765", "priority" : 1, "processing" : None, "max_size" : 3 }]
        transcriptions = [{ "assignment_id" : "21B85OZIZEHRPTEQZZH5HWPXNKOBZK", "audio_clip_id" : "12345", "worker_id" : "A2WBBX5KW5W6GY", "status" : "Submitted", "transcription" : "This is the first transcription." },
                          { "assignment_id" : "21B85OZIZEHRPTEQZZH5HWPXNKOBZK", "audio_clip_id" : "12345.0", "worker_id" : "A2WBBX5KW5W6GY", "status" : "Submitted", "transcription" : "This is the second transcription.|This is the third transcription." }]
    
def main():
    mh = MongoHandler()
    t = Turker(5)
    print(t.get_mongo_entry())
    mh.insert_entity(t)
    
if __name__ == "__main__":
    main()
        
       
        
        
    