#include <iostream>
#include <vector>
using namespace std;

template <typename T>
T maxOf(const vector<T>& v) {
    T m = v[0];
    for (const auto& x : v) if (x > m) m = x;
    return m;
}

class Counter {
public:
    int count = 0;
    void inc(int by) { count += by; }
    int get() const { return count; }
};

int main() {
    vector<int> v = {3, 1, 4};
    Counter c;
    auto sq = [](int x) { return x * x; };
    for (size_t i = 0; i < v.size(); ++i) {
        c.inc(v[i]);
    }
    cout << maxOf(v) << endl;
    std::string s = "abc";
    if (c.get() > 5) cout << "big"; else cout << "small";
    return 0;
}
