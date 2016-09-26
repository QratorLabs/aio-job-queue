-- MULTI-EXECUTE may be used instead (with LUA server blocks, but less
-- client-server communication)
--
-- KEYS[1] payloads table
-- KEYS[2] list (queue) of job IDs
-- ARGV[1] job ID
-- ARGV[2] job payload

local hset_result = redis.call('hset', KEYS[1], ARGV[1], ARGV[2])
local lpush_result = redis.call('lpush', KEYS[2], ARGV[1])
return {hset_result, lpush_result}
