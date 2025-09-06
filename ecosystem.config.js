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
    },
    {
      name: "bot6",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot6"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot6.log",
      out_file: "pm2_out_bot6.log",
      log_file: "pm2_combined_bot6.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot7",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot7"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot7.log",
      out_file: "pm2_out_bot7.log",
      log_file: "pm2_combined_bot7.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot8",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot8"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot8.log",
      out_file: "pm2_out_bot8.log",
      log_file: "pm2_combined_bot8.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot9",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot9"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot9.log",
      out_file: "pm2_out_bot9.log",
      log_file: "pm2_combined_bot9.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot10",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot10"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot10.log",
      out_file: "pm2_out_bot10.log",
      log_file: "pm2_combined_bot10.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot11",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot11"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot11.log",
      out_file: "pm2_out_bot11.log",
      log_file: "pm2_combined_bot11.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot12",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot12"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot12.log",
      out_file: "pm2_out_bot12.log",
      log_file: "pm2_combined_bot12.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot13",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot13"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot13.log",
      out_file: "pm2_out_bot13.log",
      log_file: "pm2_combined_bot13.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot14",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot14"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot14.log",
      out_file: "pm2_out_bot14.log",
      log_file: "pm2_combined_bot14.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: "bot15",
      script: "main.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "200M",
      env: {
        NODE_ENV: "production",
        BOT_INSTANCE: "bot15"
      },
      // Логувати тільки помилки
      error_file: "pm2_error_bot15.log",
      out_file: "pm2_out_bot15.log",
      log_file: "pm2_combined_bot15.log",
      merge_logs: true,
      
      time: true,
      restart_delay: 5000,
      max_restarts: 10
    }
  ]
}; 