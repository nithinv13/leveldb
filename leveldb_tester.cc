#include <iostream>
#include <cassert>
#include "leveldb/db.h"

using namespace std;

int main(int args, char** argv) {
    leveldb::DB* db;
    leveldb::Options options;
    options.create_if_missing = true;
    // options.error_if_exists = true;
    leveldb::Status status = leveldb::DB::Open(options, "/tmp/testdb", &db);
    assert(status.ok());
    leveldb::Slice key = "1";
    leveldb::Slice value = "one";
    leveldb::Status s;
    std::string val;
    s = db->Put(leveldb::WriteOptions(), key, value);
    if (s.ok()) s = db->Get(leveldb::ReadOptions(), key, &val);
    if (s.ok()) cout << key.ToString() << " " << val << endl;
}