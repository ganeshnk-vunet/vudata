package main

import (
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"

	"gopkg.in/yaml.v2"
)

type ModuleEPS struct {
	Name     string
	Unique   int
	Calc     string
	EPSValue float64
}

func getPeriodSeconds(period string) int {
	period = strings.TrimSpace(period)
	if strings.HasSuffix(period, "s") {
		p := strings.TrimSuffix(period, "s")
		if seconds, err := strconv.Atoi(p); err == nil && seconds > 0 {
			return seconds
		}
	}
	return 10
}

func readYAML(path string) (map[string]interface{}, error) {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var result map[string]interface{}
	if err := yaml.Unmarshal(data, &result); err != nil {
		return nil, err
	}
	return result, nil
}

func getNumUniqKey(conf map[string]interface{}) int {
	if uk, ok := conf["uniquekey"].(map[interface{}]interface{}); ok {
		switch n := uk["NumUniqKey"].(type) {
		case int:
			return n
		case int64:
			return int(n)
		case float64:
			return int(n)
		case string:
			if val, err := strconv.Atoi(n); err == nil {
				return val
			}
		}
	}
	return 1
}

// Open file in default browser
func openBrowser(url string) error {
	var cmd string
	var args []string

	switch runtime.GOOS {
	case "linux":
		cmd = "xdg-open"
		args = []string{url}
	case "windows":
		cmd = "cmd"
		args = []string{"/c", "start", "", url}
	case "darwin":
		cmd = "open"
		args = []string{url}
	default:
		return fmt.Errorf("unsupported platform")
	}

	return exec.Command(cmd, args...).Start()
}

func main() {
	confPath := "conf.yml"
	modDir := "./"
	mainConf, err := readYAML(confPath)
	if err != nil {
		fmt.Println("Error reading main config:", err)
		os.Exit(1)
	}

	mainKeys := getNumUniqKey(mainConf)
	period := "10s"
	if p, ok := mainConf["period"].(string); ok {
		period = p
	}
	periodSec := getPeriodSeconds(period)

	submodules := []string{}
	if sm, ok := mainConf["Include_sub_modules"].([]interface{}); ok {
		for _, s := range sm {
			submodules = append(submodules, fmt.Sprintf("%v", s))
		}
	} else if smStr, ok := mainConf["Include_sub_modules"].(string); ok {
		smStr = strings.Trim(smStr, "[]")
		for _, s := range strings.Split(smStr, ",") {
			submodules = append(submodules, strings.TrimSpace(s))
		}
	}

	var modules []ModuleEPS
	totalEPS := 0.0

	for _, sub := range submodules {
		confPath := fmt.Sprintf("%s/%s.yml", modDir, sub)
		subConf, err := readYAML(confPath)
		if err != nil {
			modules = append(modules, ModuleEPS{sub, 0, "Error", 0})
			continue
		}
		subKeys := getNumUniqKey(subConf)
		eps := float64(mainKeys*subKeys) / float64(periodSec)
		totalEPS += eps
		calc := fmt.Sprintf("%d × %d / %d", mainKeys, subKeys, periodSec)
		modules = append(modules, ModuleEPS{sub, subKeys, calc, eps})
	}

	// HTML content
	html := `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SQL Server EPS Dashboard</title>
<style>
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#f5f5f5; padding:20px; }
h1 { text-align:center; color:#333; }
table { width:100%; border-collapse:collapse; margin-top:20px; box-shadow:0 0 10px rgba(0,0,0,0.1);}
th, td { padding:12px; text-align:left; border-bottom:1px solid #ddd; }
th { background:#007BFF; color:white; }
tr:nth-child(even) { background:#e9ecef; }
tr:hover { background:#d1ecf1; }
tfoot td { font-weight:bold; background:#28a745; color:white; }
</style>
</head>
<body>
<h1>SQL Server EPS Dashboard</h1>
<table>
<thead>
<tr><th>Module</th><th>UniqueKey</th><th>EPS Calculation</th><th>EPS Value</th></tr>
</thead>
<tbody>`

	for _, m := range modules {
		html += fmt.Sprintf("<tr><td>%s</td><td>%d</td><td>%s</td><td>%.2f</td></tr>\n", m.Name, m.Unique, m.Calc, m.EPSValue)
	}

	html += fmt.Sprintf(`</tbody>
<tfoot>
<tr><td>TOTAL</td><td></td><td></td><td>%.2f</td></tr>
</tfoot>
</table>
</body>
</html>`, totalEPS)

	// Overwrite existing file
	filePath := "dashboard.html"
	err = ioutil.WriteFile(filePath, []byte(html), 0644)
	if err != nil {
		fmt.Println("Error writing HTML file:", err)
		os.Exit(1)
	}

	fmt.Println("✅ Dashboard generated:", filePath)

	// Open automatically in default browser
	err = openBrowser(filePath)
	if err != nil {
		fmt.Println("Error opening browser:", err)
	}
}
