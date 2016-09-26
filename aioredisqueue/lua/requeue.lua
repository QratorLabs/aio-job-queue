-- KEYS[1] ack table
-- KEYS[2] main queue
-- ARGV[1] requeue jobs less than this numeric value

local job_id, v, r
local results_hdel = {}
local results_lpush = {}
local results_keys = {}
local min_val = tonumber(ARGV[1])
local kvs = redis.call('HGETALL', KEYS[1])

for i = 1, #kvs, 2 do
    job_id = kvs[i]
    v = tonumber(kvs[i + 1])
    if v < min_val then
        r = redis.call('hdel', KEYS[1], job_id)
        table.insert(results_hdel, r)
        if r then
            table.insert(results_lpush, redis.call('lpush', KEYS[2], job_id))
        else
            -- Actually, that should never happen. But let's say we are looking
            -- into the bright future of multithreaded redis
            table.insert(results_lpush, -1)
        end
        table.insert(results_keys, job_id)
    end
end

return {results_hdel, results_lpush, results_keys}
