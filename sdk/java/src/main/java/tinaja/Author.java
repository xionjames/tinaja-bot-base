package tinaja;

import java.util.Map;

public record Author(String id, String name, String displayName, String mention, boolean bot) {
    static Author from(Object data) {
        Map<?, ?> map = data instanceof Map<?, ?> m ? m : Map.of();
        String name = string(map, "name");
        String displayName = map.get("display_name") instanceof String s ? s : name;
        return new Author(string(map, "id"), name, displayName, string(map, "mention"), Boolean.TRUE.equals(map.get("bot")));
    }

    static String string(Map<?, ?> map, String key) {
        return map.get(key) instanceof String s ? s : "";
    }
}
