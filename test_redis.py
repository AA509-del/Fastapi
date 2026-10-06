import redis

r=redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

r.set("test_key","hello",ex=60)
val=r.get("test_key")
print("预期输出：",val)
print("存活时间：",r.ttl("test_key"))