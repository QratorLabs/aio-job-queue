-- Should be probably performed via MULTI-EXEC

-- KEYS[1] ack table
-- KEYS[2] items table
-- ARGV[1] job id

local hdel_ack_result = redis.call('hdel', KEYS[1], ARGV[1])
local hdel_item_result = redis.call('hdel', KEYS[2], ARGV[1])
return {hdel_ack_result, hdel_item_result}
