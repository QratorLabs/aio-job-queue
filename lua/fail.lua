-- Doesn't re-queues if job was acked by another worker right before the call
--
-- KEYS[1] ack table
-- KEYS[2] main queue / list
-- ARGV[1] job ID

local hdel_result, lpush_result
hdel_result = redis.call('hdel', KEYS[1], ARGV[1])
if hdel_result then
    lpush_result = redis.call('lpush', KEYS[2], ARGV[1])
    return {'ok', hdel_result, lpush_result}
else
    return {'error', hdel_result}
end
