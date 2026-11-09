package main

import "fmt"

// Sum считает сумму
func Sum(xs []int) int {
	total := 0
	for _, v := range xs {
		if v < 0 {
			continue
		}
		total += v
	}
	return total
}

type Stack struct{ items []int }

func (s *Stack) Push(x int) {
	s.items = append(s.items, x)
}

func main() {
	xs := []int{1, 2, 3}
	for i := 0; i < 3; i++ {
		fmt.Println(i)
	}
	switch n := Sum(xs); {
	case n > 5:
		fmt.Println("big")
	default:
		fmt.Println("small")
	}
	for {
		break
	}
}
