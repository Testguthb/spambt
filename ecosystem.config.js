module.exports = {
  apps: [
    {
      name: "bot1",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot1"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot1.log",
      out_file: "pm2_out_bot1.log",
      log_file: "pm2_combined_bot1.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot2",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot2"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot2.log",
      out_file: "pm2_out_bot2.log",
      log_file: "pm2_combined_bot2.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot3",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot3"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot3.log",
      out_file: "pm2_out_bot3.log",
      log_file: "pm2_combined_bot3.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot4",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot4"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot4.log",
      out_file: "pm2_out_bot4.log",
      log_file: "pm2_combined_bot4.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot5",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot5"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot5.log",
      out_file: "pm2_out_bot5.log",
      log_file: "pm2_combined_bot5.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    }
  ]
}; 