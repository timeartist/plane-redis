package hello;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

@SpringBootApplication
public class Application implements CommandLineRunner {

	@Autowired
	private StringRedisTemplate template;

	public String external_resource (String serialized_call) {
	  String reverse = "";

        for(int i = serialized_call.length() - 1; i >= 0; i--)
        {
            reverse = reverse + serialized_call.charAt(i);
        }
        return reverse;
	}

	public String cached_call_to_external_resource(String serialized_call, Integer ttl) {
		// Takes an arbitrary string `serialized_call` and attempts to find a cached value
    // in Redis for it.
		//
    // Failing that, passes `serialized_call` call into an `external resource` function,
    // takes the result and caches it in Redis with an expiration of `ttl` which defaults to 10 mins.
    ValueOperations<String, String> ops = this.template.opsForValue();
    String value = ops.get(serialized_call);

		if (ttl == null) {
			ttl = 600;
		}

    if (value == null){
			value = external_resource(serialized_call);
			ops.set(serialized_call, value);
		}

    return value;
	}

	@Override
	public void run(String... args) throws Exception {
		ValueOperations<String, String> ops = this.template.opsForValue();
		String key = "spring.boot.redis.test";
		String result = cached_call_to_external_resource(key, 600);
		System.out.println("Found key " + key + ", value=" + ops.get(key));
	}

	public static void main(String[] args) {
		// Close the context so it doesn't stay awake listening for redis
		SpringApplication.run(Application.class, args).close();
	}
}
