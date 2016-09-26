-- KEYS[1] main list / queue
-- KEYS[2] table of pending acks
-- KEYS[3] payloads table
-- ARGV[1] increasing number indicating job expiration (like timestamp)

local identifier = redis.call('rpop', KEYS[1])
if identifier then
    local hset_result = redis.call('hset', KEYS[2], identifier, ARGV[1])
    local item = redis.call('hget', KEYS[3], identifier)
    return {'ok', identifier, item, hset_result}
else
    return {'error', identifier}
end
