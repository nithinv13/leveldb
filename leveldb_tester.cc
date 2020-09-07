#include <iostream>
#include <cassert>
#include "leveldb/db.h"
#include "leveldb/write_batch.h"

using namespace std;

int main(int args, char** argv) {
    leveldb::DB* db;
    leveldb::Options options;
    options.create_if_missing = true;
    // options.error_if_exists = true;
    leveldb::Status status = leveldb::DB::Open(options, "/tmp/wisckeydb", &db);
    assert(status.ok());
    leveldb::Slice key = "1";
    leveldb::Slice val = "one";
    leveldb::Status s;
    std::string value;
    s = db->Put(leveldb::WriteOptions(), key, val);
    if (s.ok()) s = db->Get(leveldb::ReadOptions(), key, &value);
    if (s.ok()) cout << key.ToString() << " " << value << endl;

    // Atomic updates 
    leveldb::Slice key1 = "1";
    leveldb::Slice key2 = "2";
    s = db->Get(leveldb::ReadOptions(), key1, &value);
    if (s.ok()) {
        leveldb::WriteBatch batch;
        batch.Delete(key1);
        batch.Put(key2, value);
        s = db->Write(leveldb::WriteOptions(), &batch);
    }

    key = "2";
    s = db->Get(leveldb::ReadOptions(), key, &value);
    if (s.ok()) cout << key.ToString() << " " << value << endl;

    // Synchronous updates

    leveldb::WriteOptions write_options;
    write_options.sync = true;
    db->Put(write_options, "3", "three");

    key = "3";
    s = db->Get(leveldb::ReadOptions(), key, &value);
    if (s.ok()) cout << key.ToString() << " " << value << endl;

    cout << endl;

    // Iteration 

    leveldb::Iterator* it = db->NewIterator(leveldb::ReadOptions());
    for (it->SeekToFirst(); it->Valid(); it->Next()) {
    cout << it->key().ToString() << ": "  << it->value().ToString() << endl;
    }
    assert(it->status().ok());
    delete it;

    // Parameters to tune
    // Block size 
    // Compression

}